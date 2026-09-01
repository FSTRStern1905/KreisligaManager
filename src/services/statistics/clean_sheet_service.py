from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class CleanSheetService:
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
                "clean_sheets": 0,
                "failed_to_score": 0,
                "scored_matches": 0,
                "conceded_matches": 0,
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

            if home_team_id in teams:
                home = teams[
                    home_team_id
                ]

                home["played"] += 1

                if away_goals == 0:
                    home["clean_sheets"] += 1

                if home_goals == 0:
                    home["failed_to_score"] += 1

                if home_goals > 0:
                    home["scored_matches"] += 1

                if away_goals > 0:
                    home["conceded_matches"] += 1

            if away_team_id in teams:
                away = teams[
                    away_team_id
                ]

                away["played"] += 1

                if home_goals == 0:
                    away["clean_sheets"] += 1

                if away_goals == 0:
                    away["failed_to_score"] += 1

                if away_goals > 0:
                    away["scored_matches"] += 1

                if home_goals > 0:
                    away["conceded_matches"] += 1

        result: list[dict] = []

        for team in teams.values():
            played = int(
                team["played"]
            )

            clean_sheets = int(
                team["clean_sheets"]
            )

            failed_to_score = int(
                team["failed_to_score"]
            )

            scored_matches = int(
                team["scored_matches"]
            )

            conceded_matches = int(
                team["conceded_matches"]
            )

            result.append(
                {
                    **team,
                    "clean_sheet_percentage": (
                        self._percentage(
                            clean_sheets,
                            played,
                        )
                    ),
                    "failed_to_score_percentage": (
                        self._percentage(
                            failed_to_score,
                            played,
                        )
                    ),
                    "scored_percentage": (
                        self._percentage(
                            scored_matches,
                            played,
                        )
                    ),
                    "conceded_percentage": (
                        self._percentage(
                            conceded_matches,
                            played,
                        )
                    ),
                }
            )

        result.sort(
            key=lambda team: (
                -float(
                    team[
                        "clean_sheet_percentage"
                    ]
                ),
                -int(
                    team[
                        "clean_sheets"
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
            value
            / total
            * 100,
            1,
        )