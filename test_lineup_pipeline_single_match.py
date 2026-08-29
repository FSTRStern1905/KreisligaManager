from __future__ import annotations

import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.parsers.lineup_parser import (
    LineupParser,
)


DB_PATH = Path("data/database/kreisligamanager.db")

MATCH_ID = 251

TARGET_NAMES = (
    "Kevin Stöger",
    "Haris Tabakovic",
    "Rocco Reitz",
    "Joshua Kimmich",
    "Harry Edward Kane",
    "Nicolas Jackson",
)


def normalize(value: str | None) -> str:
    return " ".join(
        (value or "").casefold().split()
    )


def full_name(
    first_name: str | None,
    last_name: str | None,
) -> str:
    return " ".join(
        part
        for part in (
            first_name or "",
            last_name or "",
        )
        if part
    ).strip()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    browser = FussballDeBrowser()

    try:
        match = connection.execute(
            """
            SELECT
                m.match_id,
                m.external_id,
                m.matchday,
                ht.name AS home_team,
                at.name AS away_team
            FROM matches AS m
            INNER JOIN teams AS ht
                ON ht.team_id = m.home_team_id
            INNER JOIN teams AS at
                ON at.team_id = m.away_team_id
            WHERE m.match_id = ?
            LIMIT 1
            """,
            (MATCH_ID,),
        ).fetchone()

        if match is None:
            raise RuntimeError(
                f"Spiel {MATCH_ID} wurde nicht gefunden."
            )

        external_id = str(
            match["external_id"] or ""
        ).strip()

        if not external_id:
            raise RuntimeError(
                "Spiel besitzt keine External-ID."
            )

        print("=" * 96)
        print("LINEUP-DIAGNOSE: ROHDATEN → PARSER → DATENBANK")
        print("=" * 96)
        print(
            f"Spiel {match['match_id']} | "
            f"ST {match['matchday']} | "
            f"{match['home_team']} - "
            f"{match['away_team']}"
        )
        print(
            f"External-ID: {external_id}"
        )

        browser.start(
            headless=False,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht gestartet werden."
            )

        lineup_url = (
            "https://www.fussball.de/"
            "ajax.match.lineup/"
            "-/mode/PAGE/spiel/"
            f"{external_id}/"
            "ticker-id/selectedTickerId"
        )

        response = browser.page.request.get(
            lineup_url,
            timeout=60_000,
        )

        if not response.ok:
            raise RuntimeError(
                "Aufstellungs-AJAX fehlgeschlagen: "
                f"HTTP {response.status}"
            )

        html = response.text()

        print()
        print("=" * 96)
        print("1) ROHDATEN")
        print("=" * 96)
        print(
            f"HTML-Länge: {len(html)} Zeichen"
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        raw_player_nodes = soup.select(
            ".match-lineup a.player-wrapper"
        )

        print(
            "player-wrapper-Knoten gesamt: "
            f"{len(raw_player_nodes)}"
        )

        raw_names: list[str] = []

        for node in raw_player_nodes:
            first = node.select_one(
                ".player-name .firstname"
            )
            last = node.select_one(
                ".player-name .lastname"
            )

            name = full_name(
                first.get_text(
                    " ",
                    strip=True,
                ) if first is not None else "",
                last.get_text(
                    " ",
                    strip=True,
                ) if last is not None else "",
            )

            if name:
                raw_names.append(
                    name
                )

        for target in TARGET_NAMES:
            hits = [
                name
                for name in raw_names
                if normalize(name)
                == normalize(target)
            ]

            print(
                f"{target:<28} "
                f"Rohdaten: "
                f"{'JA' if hits else 'NEIN'}"
            )

        parser = LineupParser(
            request_context=browser.page.request,
        )

        lineup = parser.parse(
            html
        )

        parsed_players = [
            *lineup.home.starting,
            *lineup.home.substitutes,
            *lineup.away.starting,
            *lineup.away.substitutes,
        ]

        print()
        print("=" * 96)
        print("2) LINEUPPARSER")
        print("=" * 96)
        print(
            f"Heim Startelf:   "
            f"{len(lineup.home.starting)}"
        )
        print(
            f"Heim Bank:       "
            f"{len(lineup.home.substitutes)}"
        )
        print(
            f"Auswärts Startelf: "
            f"{len(lineup.away.starting)}"
        )
        print(
            f"Auswärts Bank:     "
            f"{len(lineup.away.substitutes)}"
        )
        print(
            f"Parser gesamt:    "
            f"{len(parsed_players)}"
        )

        for target in TARGET_NAMES:
            matches = [
                player
                for player in parsed_players
                if normalize(
                    full_name(
                        player.first_name,
                        player.last_name,
                    )
                )
                == normalize(target)
            ]

            print()
            print(
                f"{target}"
            )

            if not matches:
                print(
                    "  Parser: NEIN"
                )
            else:
                for player in matches:
                    print(
                        "  Parser: JA | "
                        f"external_id={player.external_id} | "
                        f"team={player.team_name} | "
                        f"starter={player.is_starting} | "
                        f"bank={player.is_substitute}"
                    )

        db_rows = connection.execute(
            """
            SELECT
                l.player_id,
                l.team_id,
                l.is_starting,
                l.shirt_number,
                p.external_id,
                p.first_name,
                p.last_name,
                t.name AS team_name
            FROM lineups AS l
            INNER JOIN players AS p
                ON p.player_id = l.player_id
            INNER JOIN teams AS t
                ON t.team_id = l.team_id
            WHERE l.match_id = ?
            ORDER BY
                l.team_id,
                l.is_starting DESC,
                l.lineup_id
            """,
            (MATCH_ID,),
        ).fetchall()

        print()
        print("=" * 96)
        print("3) DATENBANK-LINEUP")
        print("=" * 96)
        print(
            f"Lineup-Zeilen gesamt: "
            f"{len(db_rows)}"
        )

        for target in TARGET_NAMES:
            matches = [
                row
                for row in db_rows
                if normalize(
                    full_name(
                        row["first_name"],
                        row["last_name"],
                    )
                )
                == normalize(target)
            ]

            print()
            print(
                f"{target}"
            )

            if not matches:
                print(
                    "  DB-Lineup: NEIN"
                )
            else:
                for row in matches:
                    print(
                        "  DB-Lineup: JA | "
                        f"player_id={row['player_id']} | "
                        f"external_id={row['external_id']} | "
                        f"team={row['team_name']} | "
                        f"starter={row['is_starting']}"
                    )

        print()
        print("=" * 96)
        print("4) VERLUSTSTUFE")
        print("=" * 96)

        parsed_names = {
            normalize(
                full_name(
                    player.first_name,
                    player.last_name,
                )
            )
            for player in parsed_players
        }

        db_names = {
            normalize(
                full_name(
                    row["first_name"],
                    row["last_name"],
                )
            )
            for row in db_rows
        }

        raw_name_set = {
            normalize(name)
            for name in raw_names
        }

        for target in TARGET_NAMES:
            key = normalize(target)

            in_raw = key in raw_name_set
            in_parser = key in parsed_names
            in_db = key in db_names

            if not in_raw:
                stage = (
                    "FEHLT BEREITS IN FUSSBALL.DE-ROHDATEN"
                )
            elif not in_parser:
                stage = (
                    "GEHT IM LINEUPPARSER VERLOREN"
                )
            elif not in_db:
                stage = (
                    "GEHT BEIM DB-IMPORT VERLOREN"
                )
            else:
                stage = "DURCHGÄNGIG VORHANDEN"

            print(
                f"{target:<28} {stage}"
            )

        print()
        print("=" * 96)
        print("DIAGNOSE ENDE")
        print("=" * 96)

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()
