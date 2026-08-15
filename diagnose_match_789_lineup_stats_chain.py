from __future__ import annotations

import sqlite3
from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.lineup_importer import (
    LineupImporter,
)
from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

MATCH_ID = 789

EXTERNAL_MATCH_ID = (
    "031BG6B7PG000000VS5489BUVUR5FS5A"
)

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "fc-energie-cottbus-hannover-96/-/spiel/"
    f"{EXTERNAL_MATCH_ID}#!/"
)


def count_rows(
    connection: sqlite3.Connection,
    table: str,
) -> int:
    return int(
        connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE match_id = ?
            """,
            (MATCH_ID,),
        ).fetchone()[0]
    )


def print_lineups(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        """
        SELECT
            l.lineup_id,
            l.team_id,
            t.name AS team_name,
            l.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            l.is_starting,
            l.shirt_number
        FROM lineups AS l
        LEFT JOIN teams AS t
            ON t.team_id = l.team_id
        LEFT JOIN players AS p
            ON p.player_id = l.player_id
        WHERE l.match_id = ?
        ORDER BY
            l.team_id,
            l.is_starting DESC,
            l.lineup_id
        """,
        (MATCH_ID,),
    ).fetchall()

    print("=" * 120)
    print("LINEUPS IN DB")
    print("=" * 120)

    for row in rows:
        name = " ".join(
            part
            for part in (
                row["first_name"] or "",
                row["last_name"] or "",
            )
            if part
        ) or "-"

        print(
            f"lineup_id={row['lineup_id']:<4} | "
            f"team_id={row['team_id']:<3} "
            f"({row['team_name'] or '-'}) | "
            f"player_id={row['player_id']:<4} | "
            f"start={row['is_starting']} | "
            f"Nr={row['shirt_number']} | "
            f"{name} | "
            f"external_id={row['external_id'] or '-'}"
        )

    print()
    print(
        f"Lineup-Zeilen gesamt: {len(rows)}"
    )
    print()


def print_stats(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        """
        SELECT
            pms.player_match_stat_id,
            pms.team_id,
            t.name AS team_name,
            pms.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            pms.is_starting,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played,
            pms.goals,
            pms.own_goals,
            pms.yellow_cards,
            pms.yellow_red_cards,
            pms.red_cards
        FROM player_match_stats AS pms
        LEFT JOIN teams AS t
            ON t.team_id = pms.team_id
        LEFT JOIN players AS p
            ON p.player_id = pms.player_id
        WHERE pms.match_id = ?
        ORDER BY
            pms.team_id,
            pms.is_starting DESC,
            pms.player_match_stat_id
        """,
        (MATCH_ID,),
    ).fetchall()

    print("=" * 120)
    print("PLAYER_MATCH_STATS")
    print("=" * 120)

    total_goals = 0
    total_yellow = 0

    for row in rows:
        name = " ".join(
            part
            for part in (
                row["first_name"] or "",
                row["last_name"] or "",
            )
            if part
        ) or "-"

        goals = int(
            row["goals"] or 0
        )
        own_goals = int(
            row["own_goals"] or 0
        )
        yellow = int(
            row["yellow_cards"] or 0
        )

        total_goals += goals + own_goals
        total_yellow += yellow

        print(
            f"stat_id={row['player_match_stat_id']:<4} | "
            f"team_id={row['team_id']:<3} | "
            f"player_id={row['player_id']:<4} | "
            f"start={row['is_starting']} | "
            f"in={row['minute_in']} | "
            f"out={row['minute_out']} | "
            f"min={row['minutes_played']} | "
            f"G={goals} | "
            f"YG={yellow} | "
            f"{name}"
        )

    print()
    print(
        f"Stats-Zeilen: {len(rows)}"
    )
    print(
        f"Tore in Stats: {total_goals}"
    )
    print(
        f"Gelbe Karten in Stats: {total_yellow}"
    )
    print()


def print_event_player_comparison(
    connection: sqlite3.Connection,
) -> None:
    print("=" * 120)
    print("EVENT-SPIELER VS. LINEUP-SPIELER")
    print("=" * 120)

    rows = connection.execute(
        """
        SELECT DISTINCT
            e.player_id AS event_player_id,
            ep.first_name AS event_first_name,
            ep.last_name AS event_last_name,
            ep.external_id AS event_external_id,
            e.team_id,
            et.code,
            e.notes
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN players AS ep
            ON ep.player_id = e.player_id
        WHERE
            e.match_id = ?
            AND e.player_id IS NOT NULL
        ORDER BY
            e.team_id,
            e.player_id
        """,
        (MATCH_ID,),
    ).fetchall()

    mismatch_count = 0

    for row in rows:
        event_name = " ".join(
            part
            for part in (
                row["event_first_name"] or "",
                row["event_last_name"] or "",
            )
            if part
        ) or "-"

        lineup_match = connection.execute(
            """
            SELECT
                l.player_id,
                p.first_name,
                p.last_name,
                p.external_id
            FROM lineups AS l
            LEFT JOIN players AS p
                ON p.player_id = l.player_id
            WHERE
                l.match_id = ?
                AND l.team_id = ?
                AND (
                    LOWER(TRIM(
                        COALESCE(p.first_name, '') || ' ' ||
                        COALESCE(p.last_name, '')
                    )) = LOWER(TRIM(?))
                    OR LOWER(TRIM(
                        COALESCE(p.last_name, '')
                    )) = LOWER(TRIM(?))
                )
            LIMIT 1
            """,
            (
                MATCH_ID,
                row["team_id"],
                event_name,
                event_name,
            ),
        ).fetchone()

        status = "OK"

        if (
            lineup_match is not None
            and int(lineup_match["player_id"])
            != int(row["event_player_id"])
        ):
            status = "DOPPELTE PLAYER-ID"
            mismatch_count += 1

        elif lineup_match is None:
            status = "NICHT IM LINEUP"
            mismatch_count += 1

        print(
            f"{status:<20} | "
            f"event_player_id={row['event_player_id']:<4} | "
            f"team_id={row['team_id']} | "
            f"{event_name:<42} | "
            f"event_ext={row['event_external_id'] or '-'}"
        )

        if lineup_match is not None:
            lineup_name = " ".join(
                part
                for part in (
                    lineup_match["first_name"] or "",
                    lineup_match["last_name"] or "",
                )
                if part
            ) or "-"

            print(
                f"{'':20}   "
                f"lineup_player_id={lineup_match['player_id']} | "
                f"{lineup_name} | "
                f"lineup_ext={lineup_match['external_id'] or '-'}"
            )

    print()
    print(
        f"Abweichungen Event ↔ Lineup: {mismatch_count}"
    )
    print()


def main() -> None:
    print("=" * 120)
    print("DIAGNOSE LINEUP → STATS KETTE SPIEL 789")
    print("=" * 120)

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    browser = FussballDeBrowser()

    try:
        print()
        print("DB VORHER")
        print("-" * 120)
        print(
            f"lineups:            "
            f"{count_rows(connection, 'lineups')}"
        )
        print(
            f"player_match_stats: "
            f"{count_rows(connection, 'player_match_stats')}"
        )
        print()

        browser.start(
            headless=True,
        )

        browser.open(
            MATCH_URL
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite nicht verfügbar."
            )

        print("LINEUP IMPORT")
        print("-" * 120)

        lineup_result = LineupImporter(
            connection
        ).import_from_page(
            page=browser.page,
            match_external_id=EXTERNAL_MATCH_ID,
        )

        for key, value in lineup_result.items():
            print(
                f"{key}: {value}"
            )

        print()

        print_lineups(
            connection
        )

        print_event_player_comparison(
            connection
        )

        print("STATS BUILDER")
        print("-" * 120)

        stats_result = PlayerMatchStatsBuilder(
            connection
        ).build(
            MATCH_ID
        )

        for key, value in stats_result.items():
            print(
                f"{key}: {value}"
            )

        print()

        print_stats(
            connection
        )

        print("=" * 120)
        print("ERGEBNIS")
        print("=" * 120)

        lineup_count = count_rows(
            connection,
            "lineups",
        )
        stats_count = count_rows(
            connection,
            "player_match_stats",
        )

        if lineup_count == 0:
            print(
                "FEHLER: LineupImporter schreibt weiterhin "
                "keine Aufstellungszeilen."
            )
        elif stats_count == 0:
            print(
                "FEHLER: Lineups sind vorhanden, aber "
                "PlayerMatchStatsBuilder erzeugt keine Stats."
            )
        else:
            print(
                "Kette läuft: Lineups und player_match_stats "
                "wurden erzeugt."
            )

        print("=" * 120)

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()
