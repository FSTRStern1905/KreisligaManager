import sqlite3


class MatchesTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER,
                season_id INTEGER NOT NULL,
                league_id INTEGER,
                matchday INTEGER,
                match_date TEXT,
                kickoff_time TEXT,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                stadium_id INTEGER,
                referee_id INTEGER,
                attendance INTEGER,
                home_goals INTEGER,
                away_goals INTEGER,
                status TEXT NOT NULL DEFAULT 'scheduled',
                detail_imported INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                external_id TEXT,

                FOREIGN KEY (competition_id)
                    REFERENCES competitions(competition_id),

                FOREIGN KEY (season_id)
                    REFERENCES seasons(season_id),

                FOREIGN KEY (league_id)
                    REFERENCES leagues(league_id),

                FOREIGN KEY (home_team_id)
                    REFERENCES teams(team_id),

                FOREIGN KEY (away_team_id)
                    REFERENCES teams(team_id),

                FOREIGN KEY (stadium_id)
                    REFERENCES stadiums(stadium_id),

                FOREIGN KEY (referee_id)
                    REFERENCES referees(referee_id)
            );
            """
        )

        self._ensure_detail_imported_column()

    def _ensure_detail_imported_column(
        self,
    ) -> None:
        self.cursor.execute(
            """
            PRAGMA table_info(matches);
            """
        )

        existing_columns = {
            str(row[1])
            for row in self.cursor.fetchall()
        }

        if "detail_imported" in existing_columns:
            return

        self.cursor.execute(
            """
            ALTER TABLE matches
            ADD COLUMN detail_imported
                INTEGER NOT NULL DEFAULT 0;
            """
        )