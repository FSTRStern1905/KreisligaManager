from __future__ import annotations

import sqlite3


class MatchdayStatisticsService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_statistics(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        self.cursor.execute(
            """
            SELECT
                matchday,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND matchday IS NOT NULL
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

        matchdays: dict[int, dict] = {}

        for (
            matchday,
            home_goals,
            away_goals,
        ) in self.cursor.fetchall():
            matchday = int(
                matchday
            )

            home_goals = int(
                home_goals
            )

            away_goals = int(
                away_goals
            )

            if matchday not in matchdays:
                matchdays[
                    matchday
                ] = {
                    "matchday": matchday,
                    "matches": 0,
                    "goals": 0,
                    "home_goals": 0,
                    "away_goals": 0,
                    "home_wins": 0,
                    "draws": 0,
                    "away_wins": 0,
                }

            data = matchdays[
                matchday
            ]

            data[
                "matches"
            ] += 1

            data[
                "goals"
            ] += (
                home_goals
                + away_goals
            )

            data[
                "home_goals"
            ] += home_goals

            data[
                "away_goals"
            ] += away_goals

            if home_goals > away_goals:
                data[
                    "home_wins"
                ] += 1

            elif home_goals < away_goals:
                data[
                    "away_wins"
                ] += 1

            else:
                data[
                    "draws"
                ] += 1

        result: list[dict] = []

        for data in matchdays.values():
            matches = int(
                data[
                    "matches"
                ]
            )

            goals = int(
                data[
                    "goals"
                ]
            )

            home_wins = int(
                data[
                    "home_wins"
                ]
            )

            draws = int(
                data[
                    "draws"
                ]
            )

            away_wins = int(
                data[
                    "away_wins"
                ]
            )

            result.append(
                {
                    **data,

                    "goals_per_match": (
                        self._average(
                            goals,
                            matches,
                        )
                    ),

                    "home_win_percentage": (
                        self._percentage(
                            home_wins,
                            matches,
                        )
                    ),

                    "draw_percentage": (
                        self._percentage(
                            draws,
                            matches,
                        )
                    ),

                    "away_win_percentage": (
                        self._percentage(
                            away_wins,
                            matches,
                        )
                    ),
                }
            )

        result.sort(
            key=lambda row: (
                int(
                    row[
                        "matchday"
                    ]
                )
            )
        )

        return result

    def get_summary(
        self,
        competition_id: int,
    ) -> dict:
        statistics = self.get_statistics(
            competition_id
        )

        if not statistics:
            return {
                "matchdays": 0,
                "matches": 0,
                "goals": 0,
                "goals_per_match": 0.0,
                "highest_scoring_matchday": None,
                "lowest_scoring_matchday": None,
            }

        total_matches = sum(
            int(
                row[
                    "matches"
                ]
            )
            for row in statistics
        )

        total_goals = sum(
            int(
                row[
                    "goals"
                ]
            )
            for row in statistics
        )

        highest_scoring_matchday = max(
            statistics,
            key=lambda row: (
                int(
                    row[
                        "goals"
                    ]
                ),
                -int(
                    row[
                        "matchday"
                    ]
                ),
            ),
        )

        lowest_scoring_matchday = min(
            statistics,
            key=lambda row: (
                int(
                    row[
                        "goals"
                    ]
                ),
                int(
                    row[
                        "matchday"
                    ]
                ),
            ),
        )

        return {
            "matchdays": len(
                statistics
            ),
            "matches": total_matches,
            "goals": total_goals,
            "goals_per_match": (
                self._average(
                    total_goals,
                    total_matches,
                )
            ),
            "highest_scoring_matchday": (
                highest_scoring_matchday
            ),
            "lowest_scoring_matchday": (
                lowest_scoring_matchday
            ),
        }

    @staticmethod
    def _average(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            value
            / total,
            2,
        )

    @staticmethod
    def _percentage(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            value
            / total
            * 100,
            1,
        )