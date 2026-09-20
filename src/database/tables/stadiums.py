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
                postal_code TEXT,
                federal_state TEXT,
                latitude REAL,
                longitude REAL,
                external_id TEXT
            );
            """
        )

        self._ensure_location_columns()

    def _ensure_location_columns(self) -> None:
        self.cursor.execute(
            "PRAGMA table_info(stadiums);"
        )

        columns = {
            row[1]
            for row in self.cursor.fetchall()
        }

        required_columns = {
            "postal_code": "TEXT",
            "federal_state": "TEXT",
        }

        for (
            column_name,
            column_definition,
        ) in required_columns.items():
            if column_name in columns:
                continue

            self.cursor.execute(
                f"""
                ALTER TABLE stadiums
                ADD COLUMN {column_name}
                {column_definition};
                """
            )
