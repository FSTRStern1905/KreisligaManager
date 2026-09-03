import sqlite3


class TeamSeasonMetricsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS team_season_metrics (
                team_season_metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,

                average_attendance REAL NOT NULL DEFAULT 0.0,

                goalkeeper_strength REAL NOT NULL DEFAULT 0.0,
                defense_strength REAL NOT NULL DEFAULT 0.0,
                midfield_strength REAL NOT NULL DEFAULT 0.0,
                attack_strength REAL NOT NULL DEFAULT 0.0,
                overall_strength REAL NOT NULL DEFAULT 0.0,

                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (competition_id)
                    REFERENCES competitions(competition_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (season_id)
                    REFERENCES seasons(season_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE CASCADE,

                UNIQUE (
                    competition_id,
                    team_id
                )
            );
            """
        )
