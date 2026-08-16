from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.importer.fussballde.liveticker_parser import LivetickerParser


DATABASE_PATH = Path("data/database/kreisligamanager.db")
MATCH_ID = 789
EXTERNAL_MATCH_ID = "031BG6B7PG000000VS5489BUVUR5FS5A"
JSON_PATH = Path("debug/liveticker/json") / f"{EXTERNAL_MATCH_ID}.json"


def normalize_name(value: str) -> str:
    return " ".join((value or "").split()).casefold()


def load_liveticker_data():
    payload = json.loads(
        JSON_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )
    return LivetickerParser().parse_auto(
        content=payload,
        match_id=EXTERNAL_MATCH_ID,
    )


def get_match(connection: sqlite3.Connection) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT match_id, home_team_id, away_team_id
        FROM matches
        WHERE match_id = ?
        """,
        (MATCH_ID,),
    ).fetchone()

    if row is None:
        raise RuntimeError("Spiel 789 wurde nicht gefunden.")

    return row


def get_lineup_players(
    connection: sqlite3.Connection,
    team_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            l.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            l.is_starting,
            l.shirt_number
        FROM lineups AS l
        INNER JOIN players AS p
            ON p.player_id = l.player_id
        WHERE
            l.match_id = ?
            AND l.team_id = ?
        ORDER BY
            l.is_starting DESC,
            l.shirt_number,
            l.player_id
        """,
        (MATCH_ID, team_id),
    ).fetchall()


def build_liveticker_players(
    liveticker_data,
    external_to_internal_team: dict[str, int],
) -> list[dict]:
    players: dict[tuple[int, str], dict] = {}

    for event in liveticker_data.events:
        team_external_id = (event.team or "").strip()
        internal_team_id = external_to_internal_team.get(team_external_id)

        if internal_team_id is None:
            continue

        for name, external_id in (
            (event.player, event.player_id),
            (event.player_out, event.player_out_id),
        ):
            normalized = normalize_name(name)

            if not normalized:
                continue

            key = (internal_team_id, normalized)

            if key not in players:
                players[key] = {
                    "team_id": internal_team_id,
                    "name": " ".join((name or "").split()),
                    "external_ids": set(),
                }

            normalized_external_id = (external_id or "").strip()

            if normalized_external_id:
                players[key]["external_ids"].add(normalized_external_id)

    return list(players.values())


def find_lineup_matches(
    lineup_rows: list[sqlite3.Row],
    liveticker_name: str,
) -> list[sqlite3.Row]:
    target = normalize_name(liveticker_name)
    exact: list[sqlite3.Row] = []
    relaxed: list[sqlite3.Row] = []

    for row in lineup_rows:
        first_name = (row["first_name"] or "").strip()
        last_name = (row["last_name"] or "").strip()

        full_name = normalize_name(f"{first_name} {last_name}")
        reverse_name = normalize_name(f"{last_name} {first_name}")
        normalized_first = normalize_name(first_name)
        normalized_last = normalize_name(last_name)

        if target in {full_name, reverse_name}:
            exact.append(row)
            continue

        if target and (
            target == normalized_first
            or target == normalized_last
        ):
            relaxed.append(row)
            continue

        shorter = (
            full_name
            if len(full_name) <= len(target)
            else target
        )
        longer = (
            target
            if len(target) >= len(full_name)
            else full_name
        )

        shorter_tokens = shorter.split()

        if (
            len(shorter_tokens) >= 2
            and len(shorter) >= 8
            and longer.startswith(
                shorter + " "
            )
        ):
            relaxed.append(row)

    return exact if exact else relaxed


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        match = get_match(connection)
        home_team_id = int(match["home_team_id"])
        away_team_id = int(match["away_team_id"])
        liveticker_data = load_liveticker_data()

        team_external_ids = sorted(
            {
                (event.team or "").strip()
                for event in liveticker_data.events
                if (event.team or "").strip()
            }
        )

        if len(team_external_ids) != 2:
            raise RuntimeError(
                "Es wurden nicht genau zwei Liveticker-Team-IDs gefunden."
            )

        goal_events = [
            event
            for event in liveticker_data.events
            if (
                event.event_type in {"goal", "own_goal", "penalty_goal"}
                and event.team
                and event.score_home is not None
                and event.score_away is not None
            )
        ]

        goal_events.sort(
            key=lambda event: (
                event.minute if event.minute is not None else 999,
                event.additional_time,
            )
        )

        external_to_internal_team: dict[str, int] = {}
        previous_home = 0
        previous_away = 0

        for event in goal_events:
            current_home = int(event.score_home)
            current_away = int(event.score_away)

            home_delta = current_home - previous_home
            away_delta = current_away - previous_away
            team_external_id = (event.team or "").strip()

            if home_delta > 0 and away_delta <= 0:
                external_to_internal_team[team_external_id] = home_team_id
            elif away_delta > 0 and home_delta <= 0:
                external_to_internal_team[team_external_id] = away_team_id

            previous_home = max(previous_home, current_home)
            previous_away = max(previous_away, current_away)

        if len(external_to_internal_team) == 1:
            known_external_id = next(iter(external_to_internal_team))
            known_internal_id = external_to_internal_team[known_external_id]

            other_external_id = next(
                item
                for item in team_external_ids
                if item != known_external_id
            )

            external_to_internal_team[other_external_id] = (
                away_team_id
                if known_internal_id == home_team_id
                else home_team_id
            )

        print("=" * 120)
        print("DIAGNOSE SPIELER-MAPPING LIVETICKER ↔ LINEUP")
        print("=" * 120)
        print(f"Spiel-ID: {MATCH_ID}")
        print(f"Teams intern: {home_team_id} / {away_team_id}")
        print()

        print("TEAM-MAPPING")
        print("-" * 120)

        for external_id in team_external_ids:
            print(
                f"{external_id} → "
                f"team_id={external_to_internal_team.get(external_id)}"
            )

        print()

        liveticker_players = build_liveticker_players(
            liveticker_data,
            external_to_internal_team,
        )

        total = 0
        match_count = 0
        ambiguous_count = 0
        missing_count = 0

        for team_id in (home_team_id, away_team_id):
            lineup_rows = get_lineup_players(connection, team_id)
            team_players = [
                player
                for player in liveticker_players
                if player["team_id"] == team_id
            ]

            print("=" * 120)
            print(f"TEAM {team_id}")
            print("=" * 120)

            for player in sorted(
                team_players,
                key=lambda item: normalize_name(item["name"]),
            ):
                total += 1
                matches = find_lineup_matches(
                    lineup_rows,
                    player["name"],
                )

                if len(matches) == 1:
                    status = "MATCH"
                    match_count += 1
                elif len(matches) > 1:
                    status = "MEHRDEUTIG"
                    ambiguous_count += 1
                else:
                    status = "KEIN MATCH"
                    missing_count += 1

                member_ids = ", ".join(
                    sorted(player["external_ids"])
                ) or "-"

                print(
                    f"{status:<11} | "
                    f"{player['name']:<45} | "
                    f"member_id={member_ids}"
                )

                for row in matches:
                    lineup_name = " ".join(
                        part
                        for part in (
                            row["first_name"] or "",
                            row["last_name"] or "",
                        )
                        if part
                    )

                    print(
                        f"{'':11}   "
                        f"→ player_id={row['player_id']} | "
                        f"{lineup_name} | "
                        f"external_id={row['external_id'] or '-'} | "
                        f"start={row['is_starting']} | "
                        f"Nr={row['shirt_number']}"
                    )

            print()

        print("=" * 120)
        print("ZUSAMMENFASSUNG")
        print("=" * 120)
        print(f"Liveticker-Spieler: {total}")
        print(f"Eindeutige Matches: {match_count}")
        print(f"Mehrdeutig:          {ambiguous_count}")
        print(f"Kein Match:          {missing_count}")
        print()

        if total > 0 and match_count == total:
            print(
                "ERGEBNIS: Alle Liveticker-Spieler lassen sich "
                "eindeutig auf Lineup-Spieler abbilden."
            )
        else:
            print(
                "ERGEBNIS: Für einzelne Spieler sind zusätzliche "
                "Matching-Regeln nötig."
            )

        print("=" * 120)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
