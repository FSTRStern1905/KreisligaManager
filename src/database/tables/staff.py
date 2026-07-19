import sqlite3


class StaffTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS staff (
                staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                first_name TEXT,
                last_name TEXT NOT NULL,
                role TEXT,
                email TEXT,
                phone TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                external_id TEXT,

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE SET NULL
            );
            """
        )