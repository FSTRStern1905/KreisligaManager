import sqlite3


class TeamStadiumsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS team_stadiums (
                team_stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                stadium_id INTEGER NOT NULL,
                competition_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'alternate',
                home_matches INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (stadium_id)
                    REFERENCES stadiums(stadium_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (competition_id)
                    REFERENCES competitions(competition_id)
                    ON DELETE CASCADE,

                UNIQUE (
                    team_id,
                    stadium_id,
                    competition_id
                ),

                CHECK (
                    role IN ('main', 'alternate')
                )
            );
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_team_stadiums_competition
            ON team_stadiums (
                competition_id
            );
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_team_stadiums_team
            ON team_stadiums (
                team_id
            );
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_team_stadiums_stadium
            ON team_stadiums (
                stadium_id
            );
            """
        )
