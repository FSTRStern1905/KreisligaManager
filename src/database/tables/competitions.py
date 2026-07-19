import sqlite3


class CompetitionsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS competitions (
                competition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER,
                season_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                external_id TEXT,
                FOREIGN KEY (league_id)
                    REFERENCES leagues(league_id),
                FOREIGN KEY (season_id)
                    REFERENCES seasons(season_id)
            );
            """
        )