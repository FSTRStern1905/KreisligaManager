from __future__ import annotations

import json
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

MATCH_ID = 789

EXTERNAL_MATCH_ID = (
    "031BG6B7PG000000VS5489BUVUR5FS5A"
)

JSON_PATH = Path(
    "debug/liveticker/json"
) / f"{EXTERNAL_MATCH_ID}.json"


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        print("=" * 100)
        print("DIAGNOSE TEAM-ZUORDNUNG SPIEL 789")
        print("=" * 100)

        match_row = connection.execute(
            """
            SELECT
                match_id,
                home_team_id,
                away_team_id
            FROM matches
            WHERE match_id = ?
            """,
            (MATCH_ID,),
        ).fetchone()

        if match_row is None:
            raise RuntimeError(
                "Spiel 789 nicht gefunden."
            )

        print(
            f"home_team_id: {match_row['home_team_id']}"
        )
        print(
            f"away_team_id: {match_row['away_team_id']}"
        )

        lineup_rows = connection.execute(
            """
            SELECT
                lineups.team_id,
                players.player_id,
                players.first_name,
                players.last_name,
                players.external_id
            FROM lineups
            INNER JOIN players
                ON players.player_id =
                   lineups.player_id
            WHERE lineups.match_id = ?
            ORDER BY
                lineups.team_id,
                players.last_name,
                players.first_name
            """,
            (MATCH_ID,),
        ).fetchall()

        print()
        print(
            f"Aufstellungszeilen: {len(lineup_rows)}"
        )
        print("-" * 100)

        for row in lineup_rows:
            full_name = " ".join(
                part
                for part in (
                    row["first_name"] or "",
                    row["last_name"] or "",
                )
                if part
            )

            print(
                f"team_id={row['team_id']:<3} | "
                f"player_id={row['player_id']:<4} | "
                f"external_id={row['external_id'] or '-':<40} | "
                f"{full_name}"
            )

        print()
        print("LIVETICKER MEMBER-IDs")
        print("-" * 100)

        payload = json.loads(
            JSON_PATH.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        events = []

        if isinstance(payload, dict):
            for value in payload.values():
                if isinstance(value, list):
                    if value and isinstance(
                        value[0],
                        dict,
                    ):
                        events = value
                        break

        if not events and isinstance(
            payload,
            list,
        ):
            events = payload

        seen = set()

        for event in events:
            if not isinstance(
                event,
                dict,
            ):
                continue

            team_external_id = str(
                event.get("team_id", "")
                or ""
            ).strip()

            member_id = str(
                event.get("member_id", "")
                or ""
            ).strip()

            member2_id = str(
                event.get("member2_id", "")
                or ""
            ).strip()

            description = str(
                event.get("description", "")
                or ""
            ).strip()

            signature = (
                team_external_id,
                member_id,
                member2_id,
                description,
            )

            if signature in seen:
                continue

            seen.add(signature)

            if (
                not team_external_id
                and not member_id
                and not member2_id
            ):
                continue

            print(
                f"team_ext={team_external_id or '-':<40} | "
                f"member={member_id or '-':<40} | "
                f"member2={member2_id or '-':<40} | "
                f"{description}"
            )

        print()
        print("DIREKTE MATCHES MEMBER_ID -> LINEUP")
        print("-" * 100)

        member_ids = set()

        for event in events:
            if not isinstance(
                event,
                dict,
            ):
                continue

            for key in (
                "member_id",
                "member2_id",
            ):
                value = str(
                    event.get(key, "")
                    or ""
                ).strip()

                if value:
                    member_ids.add(value)

        match_count = 0

        for member_id in sorted(
            member_ids
        ):
            row = connection.execute(
                """
                SELECT
                    lineups.team_id,
                    players.player_id,
                    players.first_name,
                    players.last_name,
                    players.external_id
                FROM players
                LEFT JOIN lineups
                    ON lineups.player_id =
                       players.player_id
                    AND lineups.match_id = ?
                WHERE players.external_id = ?
                LIMIT 1
                """,
                (
                    MATCH_ID,
                    member_id,
                ),
            ).fetchone()

            if row is None:
                continue

            match_count += 1

            name = " ".join(
                part
                for part in (
                    row["first_name"] or "",
                    row["last_name"] or "",
                )
                if part
            )

            print(
                f"{member_id} -> "
                f"player_id={row['player_id']} | "
                f"team_id={row['team_id']} | "
                f"{name}"
            )

        print()
        print(
            f"Direkte ID-Matches: {match_count}"
        )
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
