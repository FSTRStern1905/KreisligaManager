from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


def main() -> None:
    if not DATABASE_PATH.exists():
        print("Datenbank nicht gefunden.")
        return

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        print("=" * 100)
        print("COMPETITIONS + SPIELPLAN-SYNC")
        print("=" * 100)

        rows = connection.execute(
            """
            SELECT
                competition_id,
                league_id,
                season_id,
                name,
                schedule_url,
                last_schedule_sync
            FROM competitions
            ORDER BY competition_id;
            """
        ).fetchall()

        for row in rows:
            (
                competition_id,
                league_id,
                season_id,
                name,
                schedule_url,
                last_schedule_sync,
            ) = row

            print(
                f"ID={competition_id:<4} | "
                f"league_id={league_id!s:<4} | "
                f"season_id={season_id!s:<4} | "
                f"name={name!r}"
            )
            print(
                f"    URL={schedule_url!r}"
            )
            print(
                f"    Sync={last_schedule_sync!r}"
            )

        print()
        print("=" * 100)
        print("2. BUNDESLIGA-KANDIDATEN")
        print("=" * 100)

        rows = connection.execute(
            """
            SELECT
                competition_id,
                league_id,
                season_id,
                name,
                schedule_url,
                last_schedule_sync
            FROM competitions
            WHERE
                lower(name) LIKE '%bundesliga%'
            ORDER BY competition_id;
            """
        ).fetchall()

        if not rows:
            print(
                "Keine Wettbewerbe mit 'bundesliga' "
                "im Namen gefunden."
            )

        for row in rows:
            print(row)

        print()
        print("=" * 100)
        print("SPIELE PRO COMPETITION")
        print("=" * 100)

        rows = connection.execute(
            """
            SELECT
                m.competition_id,
                c.name,
                COUNT(*) AS match_count,
                MIN(m.match_date),
                MAX(m.match_date)
            FROM matches AS m
            LEFT JOIN competitions AS c
                ON c.competition_id = m.competition_id
            GROUP BY
                m.competition_id,
                c.name
            ORDER BY
                m.competition_id;
            """
        ).fetchall()

        for row in rows:
            print(row)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
