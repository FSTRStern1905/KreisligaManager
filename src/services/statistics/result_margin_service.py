from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class ResultMarginService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.table_service = TableService(
            connection
        )

    def get_statistics(
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

        teams: dict[int, dict] = {}

        for position, team in enumerate(
            table,
            start=1,
        ):
            team_id = int(
                team["team_id"]
            )

            teams[team_id] = {
                "team_id": team_id,
                "team_name": team["team_name"],
                "position": position,
                "played": 0,
                "wins_by_1": 0,
                "wins_by_2": 0,
                "wins_by_3_plus": 0,
                "losses_by_1": 0,
                "losses_by_2": 0,
                "losses_by_3_plus": 0,
                "biggest_win_margin": 0,
                "biggest_loss_margin": 0,
                "biggest_win_score": None,
                "biggest_loss_score": None,
            }

        matches = self._load_matches(
            competition_id
        )

        for match in matches:
            (
                home_team_id,
                away_team_id,
                home_goals,
                away_goals,
            ) = match

            home_team_id = int(
                home_team_id
            )

            away_team_id = int(
                away_team_id
            )

            home_goals = int(
                home_goals
            )

            away_goals = int(
                away_goals
            )

            self._apply_result(
                teams=teams,
                team_id=home_team_id,
                goals_for=home_goals,
                goals_against=away_goals,
            )

            self._apply_result(
                teams=teams,
                team_id=away_team_id,
                goals_for=away_goals,
                goals_against=home_goals,
            )

        result: list[dict] = []

        for team in teams.values():
            played = int(
                team["played"]
            )

            wins_total = (
                int(
                    team["wins_by_1"]
                )
                + int(
                    team["wins_by_2"]
                )
                + int(
                    team["wins_by_3_plus"]
                )
            )

            losses_total = (
                int(
                    team["losses_by_1"]
                )
                + int(
                    team["losses_by_2"]
                )
                + int(
                    team["losses_by_3_plus"]
                )
            )

            result.append(
                {
                    **team,
                    "wins_total": wins_total,
                    "losses_total": losses_total,
                    "close_win_percentage": (
                        self._percentage(
                            team["wins_by_1"],
                            wins_total,
                        )
                    ),
                    "big_win_percentage": (
                        self._percentage(
                            team["wins_by_3_plus"],
                            wins_total,
                        )
                    ),
                    "close_loss_percentage": (
                        self._percentage(
                            team["losses_by_1"],
                            losses_total,
                        )
                    ),
                    "heavy_loss_percentage": (
                        self._percentage(
                            team["losses_by_3_plus"],
                            losses_total,
                        )
                    ),
                    "decisive_matches": (
                        int(
                            team["wins_by_3_plus"]
                        )
                        + int(
                            team["losses_by_3_plus"]
                        )
                    ),
                    "decisive_match_percentage": (
                        self._percentage(
                            (
                                int(
                                    team["wins_by_3_plus"]
                                )
                                + int(
                                    team["losses_by_3_plus"]
                                )
                            ),
                            played,
                        )
                    ),
                }
            )

        result.sort(
            key=lambda team: (
                -int(
                    team[
                        "wins_by_3_plus"
                    ]
                ),
                -int(
                    team[
                        "biggest_win_margin"
                    ]
                ),
                int(
                    team[
                        "position"
                    ]
                    or 9999
                ),
            )
        )

        return result

    def _apply_result(
        self,
        teams: dict[int, dict],
        team_id: int,
        goals_for: int,
        goals_against: int,
    ) -> None:
        if team_id not in teams:
            return

        team = teams[
            team_id
        ]

        team["played"] += 1

        goal_difference = (
            goals_for
            - goals_against
        )

        if goal_difference > 0:
            self._apply_win(
                team=team,
                margin=goal_difference,
                goals_for=goals_for,
                goals_against=goals_against,
            )

        elif goal_difference < 0:
            self._apply_loss(
                team=team,
                margin=abs(
                    goal_difference
                ),
                goals_for=goals_for,
                goals_against=goals_against,
            )

    @staticmethod
    def _apply_win(
        team: dict,
        margin: int,
        goals_for: int,
        goals_against: int,
    ) -> None:
        if margin == 1:
            team[
                "wins_by_1"
            ] += 1

        elif margin == 2:
            team[
                "wins_by_2"
            ] += 1

        else:
            team[
                "wins_by_3_plus"
            ] += 1

        if (
            margin
            > int(
                team[
                    "biggest_win_margin"
                ]
            )
        ):
            team[
                "biggest_win_margin"
            ] = margin

            team[
                "biggest_win_score"
            ] = (
                f"{goals_for}:"
                f"{goals_against}"
            )

    @staticmethod
    def _apply_loss(
        team: dict,
        margin: int,
        goals_for: int,
        goals_against: int,
    ) -> None:
        if margin == 1:
            team[
                "losses_by_1"
            ] += 1

        elif margin == 2:
            team[
                "losses_by_2"
            ] += 1

        else:
            team[
                "losses_by_3_plus"
            ] += 1

        if (
            margin
            > int(
                team[
                    "biggest_loss_margin"
                ]
            )
        ):
            team[
                "biggest_loss_margin"
            ] = margin

            team[
                "biggest_loss_score"
            ] = (
                f"{goals_for}:"
                f"{goals_against}"
            )

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday,
                match_id
            """,
            (
                competition_id,
            ),
        )

        return self.cursor.fetchall()

    @staticmethod
    def _percentage(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            int(
                value
            )
            / total
            * 100,
            1,
        )