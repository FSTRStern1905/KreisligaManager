import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class GoalDifferenceService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.table_service = TableService(
            connection
        )

    def get_goal_differences(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        table = self.table_service.get_table(
            competition_id=competition_id,
            mode="all",
        )

        result = []

        for team in table:
            goals_for = team.get(
                "goals_for",
                0,
            )

            goals_against = team.get(
                "goals_against",
                0,
            )

            goal_difference = team.get(
                "goal_difference",
                goals_for - goals_against,
            )

            result.append(
                {
                    "team_id": team["team_id"],
                    "team_name": team["team_name"],
                    "played": team.get(
                        "played",
                        0,
                    ),
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "goal_difference": (
                        goal_difference
                    ),
                }
            )

        result.sort(
            key=lambda team: (
                -team["goal_difference"],
                -team["goals_for"],
                team["goals_against"],
                team["team_name"].lower(),
            )
        )

        for position, team in enumerate(
            result,
            start=1,
        ):
            team["position"] = position

        return result

    def get_best_goal_difference(
        self,
        competition_id: int,
    ) -> dict | None:
        teams = self.get_goal_differences(
            competition_id
        )

        if not teams:
            return None

        return teams[0]

    def get_worst_goal_difference(
        self,
        competition_id: int,
    ) -> dict | None:
        teams = self.get_goal_differences(
            competition_id
        )

        if not teams:
            return None

        return teams[-1]

    def get_average_goal_difference(
        self,
        competition_id: int,
    ) -> float:
        teams = self.get_goal_differences(
            competition_id
        )

        if not teams:
            return 0.0

        total = sum(
            team["goal_difference"]
            for team in teams
        )

        return round(
            total / len(teams),
            2,
        )