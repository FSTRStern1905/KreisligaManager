import sqlite3


class TeamsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                short_name TEXT,
                team_number INTEGER,
                coach TEXT,
                age_group TEXT,
                external_id TEXT,
                FOREIGN KEY (club_id)
                    REFERENCES clubs(club_id)
            );
            """
        )