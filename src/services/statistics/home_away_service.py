import sqlite3

from src.services.statistics.table_service import TableService


class HomeAwayService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.table_service = TableService(connection)

    def get_comparison(
        self,
        competition_id: int,
    ) -> list[dict]:
        overall_table = self.table_service.get_table(
            competition_id=competition_id,
            mode="all",
        )

        home_table = self.table_service.get_table(
            competition_id=competition_id,
            mode="home",
        )

        away_table = self.table_service.get_table(
            competition_id=competition_id,
            mode="away",
        )

        overall_by_team = {
            row["team_id"]: row
            for row in overall_table
        }

        home_by_team = {
            row["team_id"]: row
            for row in home_table
        }

        away_by_team = {
            row["team_id"]: row
            for row in away_table
        }

        comparison = []

        for team_id, overall in overall_by_team.items():
            home = home_by_team[team_id]
            away = away_by_team[team_id]

            comparison.append(
                {
                    "team_id": team_id,
                    "team_name": overall["team_name"],
                    "overall_points": overall["points"],
                    "home_points": home["points"],
                    "away_points": away["points"],
                    "home_goal_difference": (
                        home["goal_difference"]
                    ),
                    "away_goal_difference": (
                        away["goal_difference"]
                    ),
                    "point_difference": (
                        home["points"]
                        - away["points"]
                    ),
                    "goal_difference_difference": (
                        home["goal_difference"]
                        - away["goal_difference"]
                    ),
                }
            )

        comparison.sort(
            key=lambda row: (
                -abs(row["point_difference"]),
                -abs(
                    row["goal_difference_difference"]
                ),
                row["team_name"].lower(),
            )
        )

        return comparison