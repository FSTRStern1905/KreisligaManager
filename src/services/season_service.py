import sqlite3

from src.services.schedule_generator import ScheduleGenerator


class SeasonService:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.generator = ScheduleGenerator()

    def generate_schedule_for_competition(
        self,
        competition_id: int,
    ):
        competition = self._load_competition(competition_id)

        if competition is None:
            raise ValueError("Der Wettbewerb wurde nicht gefunden.")

        season_id = competition["season_id"]
        league_id = competition["league_id"]

        if self._schedule_exists(competition_id):
            raise ValueError(
                "Für diesen Wettbewerb existiert bereits ein Spielplan."
            )

        teams = self._load_competition_teams(competition_id)

        if len(teams) < 2:
            raise ValueError(
                "Dem Wettbewerb sind nicht genügend Mannschaften zugeordnet."
            )

        schedule = self.generator.generate_double_round_robin(teams)

        self._save_schedule(
            schedule=schedule,
            competition_id=competition_id,
            season_id=season_id,
            league_id=league_id,
        )

        self.connection.commit()

        return {
            "competition_id": competition_id,
            "team_count": len(teams),
            "matchday_count": len(schedule),
            "match_count": sum(
                len(matchday["matches"])
                for matchday in schedule
            ),
        }

    def _load_competition(
        self,
        competition_id: int,
    ) -> dict | None:
        self.cursor.execute(
            """
            SELECT
                competition_id,
                season_id,
                league_id,
                name
            FROM competitions
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return {
            "competition_id": row[0],
            "season_id": row[1],
            "league_id": row[2],
            "name": row[3],
        }

    def _schedule_exists(
        self,
        competition_id: int,
    ) -> bool:
        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        count = self.cursor.fetchone()[0]

        return count > 0

    def _load_competition_teams(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name
            FROM competition_teams
            INNER JOIN teams
                ON teams.team_id = competition_teams.team_id
            WHERE competition_teams.competition_id = ?
            ORDER BY teams.team_id
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def _save_schedule(
        self,
        schedule,
        competition_id: int,
        season_id: int,
        league_id: int | None,
    ):
        for matchday in schedule:
            for home, away in matchday["matches"]:
                home_id = home[0]
                away_id = away[0]

                self.cursor.execute(
                    """
                    INSERT INTO matches (
                        competition_id,
                        season_id,
                        league_id,
                        matchday,
                        home_team_id,
                        away_team_id,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        competition_id,
                        season_id,
                        league_id,
                        matchday["matchday"],
                        home_id,
                        away_id,
                        "scheduled",
                    ),
                )