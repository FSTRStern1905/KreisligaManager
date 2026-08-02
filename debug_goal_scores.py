import sqlite3


DATABASE_PATH = (
    "data/database/kreisligamanager_test.db"
)


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            events.event_id,
            events.match_id,
            event_types.code,
            events.minute,
            events.value,
            events.notes
        FROM events
        INNER JOIN event_types
            ON event_types.event_type_id =
                events.event_type_id
        WHERE
            events.match_id = 1
            AND event_types.code IN (
                'GOAL',
                'PENALTY_GOAL',
                'OWN_GOAL'
            )
        ORDER BY
            events.minute,
            events.event_id;
        """
    )

    for row in cursor.fetchall():
        print(row)

    connection.close()


if __name__ == "__main__":
    main()