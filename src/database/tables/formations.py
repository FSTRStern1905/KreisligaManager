import sqlite3


class FormationsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS formations (
                formation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                defenders INTEGER,
                midfielders INTEGER,
                forwards INTEGER,
                external_id TEXT
            );
            """
        )