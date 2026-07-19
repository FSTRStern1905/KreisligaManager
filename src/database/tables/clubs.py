import sqlite3


class ClubsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clubs (
                club_id INTEGER PRIMARY KEY AUTOINCREMENT,
                association_id INTEGER,
                name TEXT NOT NULL UNIQUE,
                short_name TEXT,
                city TEXT,
                country TEXT,
                founded INTEGER,
                website TEXT,
                logo TEXT,
                external_id TEXT,
                FOREIGN KEY (association_id)
                    REFERENCES associations(association_id)
            );
            """
        )