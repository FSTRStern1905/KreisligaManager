import sqlite3


class StadiumsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stadiums (
                stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                capacity INTEGER,
                address TEXT,
                latitude REAL,
                longitude REAL,
                external_id TEXT
            );
            """
        )