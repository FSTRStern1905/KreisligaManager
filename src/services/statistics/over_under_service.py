from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class OverUnderService:
    THRESHOLDS = (
        0.5,
        1.5,
        2.5,
        3.5,
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
                "played": 0,
                "total_goals": 0,
                "btts": 0,
                "over_0_5": 0,
                "over_1_5": 0,
                "over_2_5": 0,
                "over_3_5": 0,
                "under_0_5": 0,
                "under_1_5": 0,
                "under_2_5": 0,
                "under_3_5": 0,
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

            match_goals = (
                home_goals
                + away_goals
            )

            both_teams_scored = (
                home_goals > 0
                and away_goals > 0
            )

            self._apply_match(
                teams=teams,
                team_id=home_team_id,
                match_goals=match_goals,
                both_teams_scored=both_teams_scored,
            )

            self._apply_match(
                teams=teams,
                team_id=away_team_id,
                match_goals=match_goals,
                both_teams_scored=both_teams_scored,
            )

        result: list[dict] = []

        for team in teams.values():
            played = int(
                team["played"]
            )

            total_goals = int(
                team["total_goals"]
            )

            team_result = {
                **team,
                "average_match_goals": (
                    round(
                        total_goals
                        / played,
                        2,
                    )
                    if played > 0
                    else 0.0
                ),
                "btts_percentage": (
                    self._percentage(
                        team["btts"],
                        played,
                    )
                ),
            }

            for threshold in self.THRESHOLDS:
                suffix = self._threshold_suffix(
                    threshold
                )

                over_key = (
                    f"over_{suffix}"
                )

                under_key = (
                    f"under_{suffix}"
                )

                team_result[
                    f"{over_key}_percentage"
                ] = self._percentage(
                    team[over_key],
                    played,
                )

                team_result[
                    f"{under_key}_percentage"
                ] = self._percentage(
                    team[under_key],
                    played,
                )

            result.append(
                team_result
            )

        result.sort(
            key=lambda team: (
                -float(
                    team[
                        "over_2_5_percentage"
                    ]
                ),
                -float(
                    team[
                        "average_match_goals"
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

    def _apply_match(
        self,
        teams: dict[int, dict],
        team_id: int,
        match_goals: int,
        both_teams_scored: bool,
    ) -> None:
        if team_id not in teams:
            return

        team = teams[
            team_id
        ]

        team["played"] += 1

        team["total_goals"] += (
            match_goals
        )

        if both_teams_scored:
            team["btts"] += 1

        for threshold in self.THRESHOLDS:
            suffix = self._threshold_suffix(
                threshold
            )

            over_key = (
                f"over_{suffix}"
            )

            under_key = (
                f"under_{suffix}"
            )

            if (
                match_goals
                > threshold
            ):
                team[over_key] += 1

            else:
                team[under_key] += 1

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
    def _threshold_suffix(
        threshold: float,
    ) -> str:
        return (
            str(
                threshold
            )
            .replace(
                ".",
                "_",
            )
        )

    @staticmethod
    def _percentage(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            int(value)
            / total
            * 100,
            1,
        )