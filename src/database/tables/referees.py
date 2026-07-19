import sqlite3


class RefereesTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS referees (
                referee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT NOT NULL,
                association TEXT,
                license_level TEXT,
                email TEXT,
                phone TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                external_id TEXT
            );
            """
        )