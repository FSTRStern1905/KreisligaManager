import sqlite3


connection = sqlite3.connect(
    "data/database/kreisligamanager_test.db"
)

cursor = connection.cursor()

cursor.execute(
    """
    SELECT
        events.event_id,
        events.match_id,
        events.minute,
        events.team_id,
        events.player_id,
        events.value,
        events.notes
    FROM events
    INNER JOIN event_types
        ON event_types.event_type_id =
            events.event_type_id
    WHERE event_types.code = 'YELLOW_CARD'
    ORDER BY
        events.match_id,
        events.minute,
        events.event_id;
    """
)

for row in cursor.fetchall():
    print(row)

connection.close()