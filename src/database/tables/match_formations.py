import sqlite3


class MatchFormationsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS match_formations (
                match_formation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                formation_id INTEGER NOT NULL,

                FOREIGN KEY (match_id)
                    REFERENCES matches(match_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (formation_id)
                    REFERENCES formations(formation_id)
            );
            """
        )