from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class StreakService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.table_service = TableService(
            connection
        )

    def get_streaks(
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

        matches = self._load_matches(
            competition_id
        )

        teams: dict[int, dict] = {}

        for team in table:
            team_id = int(
                team["team_id"]
            )

            teams[team_id] = {
                "team_id": team_id,
                "team_name": team["team_name"],
                "position": None,
                "results": [],
            }

        for position, team in enumerate(
            table,
            start=1,
        ):
            team_id = int(
                team["team_id"]
            )

            if team_id in teams:
                teams[team_id][
                    "position"
                ] = position

        for match in matches:
            (
                match_id,
                matchday,
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

            home_result = (
                self._get_result(
                    goals_for=home_goals,
                    goals_against=away_goals,
                )
            )

            away_result = (
                self._get_result(
                    goals_for=away_goals,
                    goals_against=home_goals,
                )
            )

            if home_team_id in teams:
                teams[
                    home_team_id
                ]["results"].append(
                    {
                        "match_id": int(
                            match_id
                        ),
                        "matchday": (
                            int(matchday)
                            if matchday is not None
                            else None
                        ),
                        "result": home_result,
                    }
                )

            if away_team_id in teams:
                teams[
                    away_team_id
                ]["results"].append(
                    {
                        "match_id": int(
                            match_id
                        ),
                        "matchday": (
                            int(matchday)
                            if matchday is not None
                            else None
                        ),
                        "result": away_result,
                    }
                )

        result: list[dict] = []

        for team in teams.values():
            sequence = [
                row["result"]
                for row in team["results"]
            ]

            current_result = (
                sequence[-1]
                if sequence
                else None
            )

            current_length = (
                self._current_same_result_streak(
                    sequence
                )
            )

            result.append(
                {
                    "team_id": team[
                        "team_id"
                    ],
                    "team_name": team[
                        "team_name"
                    ],
                    "position": team[
                        "position"
                    ],
                    "played": len(
                        sequence
                    ),
                    "current_result": (
                        current_result
                    ),
                    "current_length": (
                        current_length
                    ),
                    "current_label": (
                        self._current_streak_label(
                            current_result,
                            current_length,
                        )
                    ),
                    "longest_win_streak": (
                        self._longest_streak(
                            sequence,
                            allowed={
                                "S",
                            },
                        )
                    ),
                    "longest_draw_streak": (
                        self._longest_streak(
                            sequence,
                            allowed={
                                "U",
                            },
                        )
                    ),
                    "longest_loss_streak": (
                        self._longest_streak(
                            sequence,
                            allowed={
                                "N",
                            },
                        )
                    ),
                    "longest_unbeaten_streak": (
                        self._longest_streak(
                            sequence,
                            allowed={
                                "S",
                                "U",
                            },
                        )
                    ),
                    "longest_winless_streak": (
                        self._longest_streak(
                            sequence,
                            allowed={
                                "U",
                                "N",
                            },
                        )
                    ),
                    "last_5": (
                        sequence[-5:]
                    ),
                }
            )

        result.sort(
            key=lambda team: (
                team[
                    "position"
                ]
                if team[
                    "position"
                ] is not None
                else 9999,
                str(
                    team[
                        "team_name"
                    ]
                ).casefold(),
            )
        )

        return result

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                match_id,
                matchday,
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
                CASE
                    WHEN matchday IS NULL
                    THEN 1
                    ELSE 0
                END,
                matchday,
                match_id
            """,
            (
                competition_id,
            ),
        )

        return self.cursor.fetchall()

    @staticmethod
    def _get_result(
        goals_for: int,
        goals_against: int,
    ) -> str:
        if goals_for > goals_against:
            return "S"

        if goals_for < goals_against:
            return "N"

        return "U"

    @staticmethod
    def _current_same_result_streak(
        sequence: list[str],
    ) -> int:
        if not sequence:
            return 0

        current_result = (
            sequence[-1]
        )

        streak = 0

        for result in reversed(
            sequence
        ):
            if result != current_result:
                break

            streak += 1

        return streak

    @staticmethod
    def _longest_streak(
        sequence: list[str],
        allowed: set[str],
    ) -> int:
        maximum = 0
        current = 0

        for result in sequence:
            if result in allowed:
                current += 1

                maximum = max(
                    maximum,
                    current,
                )

            else:
                current = 0

        return maximum

    @staticmethod
    def _current_streak_label(
        result: str | None,
        length: int,
    ) -> str:
        if result is None:
            return "-"

        if result == "S":
            if length == 1:
                return "1 Sieg"

            return (
                f"{length} Siege"
            )

        if result == "U":
            if length == 1:
                return "1 Remis"

            return (
                f"{length} Remis"
            )

        if result == "N":
            if length == 1:
                return "1 Niederlage"

            return (
                f"{length} Niederlagen"
            )

        return "-"