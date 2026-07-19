import sqlite3


class CompetitionTeamsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS competition_teams (
                competition_team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,

                FOREIGN KEY (competition_id)
                    REFERENCES competitions(competition_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE CASCADE,

                UNIQUE (competition_id, team_id)
            );
            """
        )