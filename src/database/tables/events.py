import sqlite3


class EventsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                event_type_id INTEGER NOT NULL,
                minute INTEGER,
                second INTEGER NOT NULL DEFAULT 0,
                team_id INTEGER,
                player_id INTEGER,
                related_player_id INTEGER,
                value TEXT,
                notes TEXT,
                external_id TEXT,

                FOREIGN KEY (match_id)
                    REFERENCES matches(match_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (event_type_id)
                    REFERENCES event_types(event_type_id),

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE SET NULL,

                FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE SET NULL,

                FOREIGN KEY (related_player_id)
                    REFERENCES players(player_id)
                    ON DELETE SET NULL
            );
            """
        )