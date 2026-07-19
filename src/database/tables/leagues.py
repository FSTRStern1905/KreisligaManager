import sqlite3


class LeaguesTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leagues (
                league_id INTEGER PRIMARY KEY AUTOINCREMENT,
                association_id INTEGER,
                name TEXT NOT NULL,
                level INTEGER,
                season_type TEXT,
                country TEXT,
                external_id TEXT,
                FOREIGN KEY (association_id)
                    REFERENCES associations(association_id)
            );
            """
        )