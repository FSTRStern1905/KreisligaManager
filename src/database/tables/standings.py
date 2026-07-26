import sqlite3


class StandingsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS standings (
                standing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                draws INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                goals_for INTEGER NOT NULL DEFAULT 0,
                goals_against INTEGER NOT NULL DEFAULT 0,
                goal_difference INTEGER NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'fussball.de',
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

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
