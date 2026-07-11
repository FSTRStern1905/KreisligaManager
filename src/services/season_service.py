import sqlite3

from src.services.schedule_generator import ScheduleGenerator


class SeasonService:

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.generator = ScheduleGenerator()

    def generate_schedule(self, season_id: int):
        if self._schedule_exists(season_id):
            raise ValueError("Für diese Saison existiert bereits ein Spielplan.")

        teams = self._load_teams()

        if len(teams) < 2:
            raise ValueError("Es sind nicht genügend Mannschaften vorhanden.")

        schedule = self.generator.generate_double_round_robin(teams)

        self._save_schedule(schedule, season_id)

        self.connection.commit()

    def _schedule_exists(self, season_id: int) -> bool:
        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE season_id = ?
            """,
            (season_id,),
        )

        count = self.cursor.fetchone()[0]
        return count > 0

    def _load_teams(self):
        self.cursor.execute(
            """
            SELECT
            team_id,
            name
            FROM teams
            ORDER BY team_id
            LIMIT 12
            """
        )

        return self.cursor.fetchall()

    def _save_schedule(self, schedule, season_id):
        league_id = None

        for matchday in schedule:
            for home, away in matchday["matches"]:
                home_id = home[0]
                away_id = away[0]

                self.cursor.execute(
                    """
                    INSERT INTO matches
                    (
                        season_id,
                        league_id,
                        matchday,
                        home_team_id,
                        away_team_id,
                        status
                    )
                    VALUES
                    (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        season_id,
                        league_id,
                        matchday["matchday"],
                        home_id,
                        away_id,
                        "scheduled",
                    ),
                )