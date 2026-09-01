from __future__ import annotations

import re
import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class HalftimeResultService:
    HALFTIME_PATTERN = re.compile(
        r"Halbzeit:\s*(\d+)\s*:\s*(\d+)",
        re.IGNORECASE,
    )

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

                "matches_with_halftime": 0,

                "leading_at_halftime": 0,
                "wins_after_halftime_lead": 0,
                "draws_after_halftime_lead": 0,
                "losses_after_halftime_lead": 0,

                "drawing_at_halftime": 0,
                "wins_after_halftime_draw": 0,
                "draws_after_halftime_draw": 0,
                "losses_after_halftime_draw": 0,

                "trailing_at_halftime": 0,
                "wins_after_halftime_trail": 0,
                "draws_after_halftime_trail": 0,
                "losses_after_halftime_trail": 0,
            }

        matches = self._load_matches(
            competition_id
        )

        for match in matches:
            halftime_result = (
                self._extract_halftime_result(
                    match["notes"]
                )
            )

            if halftime_result is None:
                continue

            (
                halftime_home,
                halftime_away,
            ) = halftime_result

            home_team_id = int(
                match["home_team_id"]
            )

            away_team_id = int(
                match["away_team_id"]
            )

            home_goals = int(
                match["home_goals"]
            )

            away_goals = int(
                match["away_goals"]
            )

            if (
                home_team_id not in teams
                or away_team_id not in teams
            ):
                continue

            self._apply_team_match(
                team=teams[
                    home_team_id
                ],
                halftime_goals_for=(
                    halftime_home
                ),
                halftime_goals_against=(
                    halftime_away
                ),
                final_goals_for=(
                    home_goals
                ),
                final_goals_against=(
                    away_goals
                ),
            )

            self._apply_team_match(
                team=teams[
                    away_team_id
                ],
                halftime_goals_for=(
                    halftime_away
                ),
                halftime_goals_against=(
                    halftime_home
                ),
                final_goals_for=(
                    away_goals
                ),
                final_goals_against=(
                    home_goals
                ),
            )

        result: list[dict] = []

        for team in teams.values():
            result.append(
                self._finalize_team(
                    team
                )
            )

        result.sort(
            key=lambda team: (
                -int(
                    team[
                        "points_after_halftime_trail"
                    ]
                ),
                -float(
                    team[
                        "halftime_comeback_percentage"
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

    @staticmethod
    def _apply_team_match(
        team: dict,
        halftime_goals_for: int,
        halftime_goals_against: int,
        final_goals_for: int,
        final_goals_against: int,
    ) -> None:
        team[
            "matches_with_halftime"
        ] += 1

        won = (
            final_goals_for
            > final_goals_against
        )

        drawn = (
            final_goals_for
            == final_goals_against
        )

        lost = (
            final_goals_for
            < final_goals_against
        )

        if (
            halftime_goals_for
            > halftime_goals_against
        ):
            team[
                "leading_at_halftime"
            ] += 1

            if won:
                team[
                    "wins_after_halftime_lead"
                ] += 1

            elif drawn:
                team[
                    "draws_after_halftime_lead"
                ] += 1

            elif lost:
                team[
                    "losses_after_halftime_lead"
                ] += 1

        elif (
            halftime_goals_for
            < halftime_goals_against
        ):
            team[
                "trailing_at_halftime"
            ] += 1

            if won:
                team[
                    "wins_after_halftime_trail"
                ] += 1

            elif drawn:
                team[
                    "draws_after_halftime_trail"
                ] += 1

            elif lost:
                team[
                    "losses_after_halftime_trail"
                ] += 1

        else:
            team[
                "drawing_at_halftime"
            ] += 1

            if won:
                team[
                    "wins_after_halftime_draw"
                ] += 1

            elif drawn:
                team[
                    "draws_after_halftime_draw"
                ] += 1

            elif lost:
                team[
                    "losses_after_halftime_draw"
                ] += 1

    def _finalize_team(
        self,
        team: dict,
    ) -> dict:
        leading_at_halftime = int(
            team[
                "leading_at_halftime"
            ]
        )

        wins_after_halftime_lead = int(
            team[
                "wins_after_halftime_lead"
            ]
        )

        draws_after_halftime_lead = int(
            team[
                "draws_after_halftime_lead"
            ]
        )

        losses_after_halftime_lead = int(
            team[
                "losses_after_halftime_lead"
            ]
        )

        trailing_at_halftime = int(
            team[
                "trailing_at_halftime"
            ]
        )

        wins_after_halftime_trail = int(
            team[
                "wins_after_halftime_trail"
            ]
        )

        draws_after_halftime_trail = int(
            team[
                "draws_after_halftime_trail"
            ]
        )

        drawing_at_halftime = int(
            team[
                "drawing_at_halftime"
            ]
        )

        wins_after_halftime_draw = int(
            team[
                "wins_after_halftime_draw"
            ]
        )

        points_after_halftime_trail = (
            wins_after_halftime_trail * 3
            + draws_after_halftime_trail
        )

        points_after_halftime_draw = (
            wins_after_halftime_draw * 3
            + int(
                team[
                    "draws_after_halftime_draw"
                ]
            )
        )

        dropped_points_after_halftime_lead = (
            draws_after_halftime_lead * 2
            + losses_after_halftime_lead * 3
        )

        halftime_comeback_matches = (
            wins_after_halftime_trail
            + draws_after_halftime_trail
        )

        return {
            **team,

            "lead_conversion_percentage": (
                self._percentage(
                    wins_after_halftime_lead,
                    leading_at_halftime,
                )
            ),

            "halftime_comeback_matches": (
                halftime_comeback_matches
            ),

            "halftime_comeback_percentage": (
                self._percentage(
                    halftime_comeback_matches,
                    trailing_at_halftime,
                )
            ),

            "points_after_halftime_trail": (
                points_after_halftime_trail
            ),

            "points_after_halftime_draw": (
                points_after_halftime_draw
            ),

            "dropped_points_after_halftime_lead": (
                dropped_points_after_halftime_lead
            ),

            "win_percentage_after_halftime_draw": (
                self._percentage(
                    wins_after_halftime_draw,
                    drawing_at_halftime,
                )
            ),
        }

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                match_id,
                home_team_id,
                away_team_id,
                home_goals,
                away_goals,
                notes
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
                AND notes IS NOT NULL
            ORDER BY
                matchday,
                match_id
            """,
            (
                competition_id,
            ),
        )

        columns = [
            description[0]
            for description
            in self.cursor.description
        ]

        return [
            dict(
                zip(
                    columns,
                    row,
                )
            )
            for row in self.cursor.fetchall()
        ]

    @classmethod
    def _extract_halftime_result(
        cls,
        notes,
    ) -> tuple[int, int] | None:
        if notes is None:
            return None

        text = str(
            notes
        )

        match = (
            cls.HALFTIME_PATTERN.search(
                text
            )
        )

        if match is None:
            return None

        return (
            int(
                match.group(
                    1
                )
            ),
            int(
                match.group(
                    2
                )
            ),
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