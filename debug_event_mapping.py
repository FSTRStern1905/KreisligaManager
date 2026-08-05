from __future__ import annotations

import sqlite3


DATABASE_PATH = "data/database/kreisligamanager.db"


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        rows = connection.execute(
            """
            SELECT
                e.match_id,
                et.code,
                COUNT(*) AS event_count,
                COUNT(e.player_id) AS with_player,
                SUM(
                    CASE
                        WHEN pms.player_match_stat_id
                            IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS mapped_to_stats
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id =
                    e.event_type_id
            INNER JOIN matches AS m
                ON m.match_id = e.match_id
            LEFT JOIN player_match_stats AS pms
                ON pms.match_id = e.match_id
                AND pms.player_id = e.player_id
            WHERE
                m.detail_imported = 1
                AND et.code IN (
                    'GOAL',
                    'PENALTY_GOAL',
                    'OWN_GOAL',
                    'YELLOW_CARD',
                    'YELLOW_RED_CARD',
                    'RED_CARD'
                )
            GROUP BY
                e.match_id,
                et.code
            ORDER BY
                e.match_id,
                et.code;
            """
        ).fetchall()

        print("=" * 80)
        print("EVENT-ZUORDNUNG ZU PLAYER_MATCH_STATS")
        print("=" * 80)

        for row in rows:
            print(row)

        print()
        print("=" * 80)
        print("NICHT ZUGEORDNETE TOR-EVENTS")
        print("=" * 80)

        unmapped_goals = connection.execute(
            """
            SELECT
                e.match_id,
                et.code,
                e.player_id,
                p.first_name,
                p.last_name,
                e.minute,
                e.notes
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id =
                    e.event_type_id
            INNER JOIN matches AS m
                ON m.match_id = e.match_id
            LEFT JOIN players AS p
                ON p.player_id = e.player_id
            LEFT JOIN player_match_stats AS pms
                ON pms.match_id = e.match_id
                AND pms.player_id = e.player_id
            WHERE
                m.detail_imported = 1
                AND et.code IN (
                    'GOAL',
                    'PENALTY_GOAL',
                    'OWN_GOAL'
                )
                AND pms.player_match_stat_id IS NULL
            ORDER BY
                e.match_id,
                e.minute;
            """
        ).fetchall()

        for row in unmapped_goals:
            print(row)

    finally:
        connection.close()


if __name__ == "__main__":
    main()