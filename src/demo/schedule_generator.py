import sqlite3

from src.services.season_service import SeasonService


class DemoScheduleGenerator:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def generate(self, competition_id: int) -> dict:
        service = SeasonService(self.connection)

        try:
            return service.generate_schedule_for_competition(
                competition_id
            )

        except ValueError as error:
            if "existiert bereits ein Spielplan" in str(error):
                cursor = self.connection.cursor()

                cursor.execute(
                    """
                    SELECT
                        COUNT(*),
                        COUNT(DISTINCT matchday)
                    FROM matches
                    WHERE competition_id = ?
                    """,
                    (competition_id,),
                )

                match_count, matchday_count = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM competition_teams
                    WHERE competition_id = ?
                    """,
                    (competition_id,),
                )

                team_count = cursor.fetchone()[0]

                return {
                    "competition_id": competition_id,
                    "team_count": team_count,
                    "matchday_count": matchday_count,
                    "match_count": match_count,
                }

            raise