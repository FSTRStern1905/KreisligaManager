from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class TeamRecordsExtensionService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.table_service = TableService(
            connection
        )

    def get_records(
        self,
        competition_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        overall_table = (
            self.table_service.get_table(
                competition_id=competition_id,
                mode="all",
            )
        )

        home_table = (
            self.table_service.get_table(
                competition_id=competition_id,
                mode="home",
            )
        )

        away_table = (
            self.table_service.get_table(
                competition_id=competition_id,
                mode="away",
            )
        )

        clean_sheets = (
            self._get_clean_sheet_statistics(
                competition_id
            )
        )

        return {
            "most_points": (
                self._get_record(
                    overall_table,
                    key="points",
                    highest=True,
                )
            ),
            "fewest_points": (
                self._get_record(
                    overall_table,
                    key="points",
                    highest=False,
                )
            ),
            "best_points_per_game": (
                self._get_rate_record(
                    overall_table,
                    value_key="points",
                    divisor_key="played",
                )
            ),

            "best_home_team": (
                self._get_record(
                    home_table,
                    key="points",
                    highest=True,
                )
            ),
            "worst_home_team": (
                self._get_record(
                    home_table,
                    key="points",
                    highest=False,
                )
            ),
            "most_home_wins": (
                self._get_record(
                    home_table,
                    key="wins",
                    highest=True,
                )
            ),
            "best_home_points_per_game": (
                self._get_rate_record(
                    home_table,
                    value_key="points",
                    divisor_key="played",
                )
            ),

            "best_away_team": (
                self._get_record(
                    away_table,
                    key="points",
                    highest=True,
                )
            ),
            "worst_away_team": (
                self._get_record(
                    away_table,
                    key="points",
                    highest=False,
                )
            ),
            "most_away_wins": (
                self._get_record(
                    away_table,
                    key="wins",
                    highest=True,
                )
            ),
            "best_away_points_per_game": (
                self._get_rate_record(
                    away_table,
                    value_key="points",
                    divisor_key="played",
                )
            ),

            "most_clean_sheets": (
                self._get_clean_sheet_record(
                    clean_sheets,
                    key="clean_sheets",
                    highest=True,
                )
            ),
            "fewest_clean_sheets": (
                self._get_clean_sheet_record(
                    clean_sheets,
                    key="clean_sheets",
                    highest=False,
                )
            ),
            "best_clean_sheet_rate": (
                self._get_clean_sheet_rate_record(
                    clean_sheets
                )
            ),
        }

    @staticmethod
    def _get_record(
        table: list[dict],
        key: str,
        highest: bool,
    ) -> dict | None:
        candidates = [
            row
            for row in table
            if int(
                row.get(
                    "played",
                    0,
                )
            ) > 0
        ]

        if not candidates:
            return None

        selector = (
            max
            if highest
            else min
        )

        row = selector(
            candidates,
            key=lambda item: (
                int(
                    item.get(
                        key,
                        0,
                    )
                ),
                int(
                    item.get(
                        "goal_difference",
                        0,
                    )
                ),
                int(
                    item.get(
                        "goals_for",
                        0,
                    )
                ),
            ),
        )

        return {
            "team_id": int(
                row[
                    "team_id"
                ]
            ),
            "team_name": str(
                row[
                    "team_name"
                ]
            ),
            "played": int(
                row.get(
                    "played",
                    0,
                )
            ),
            "value": int(
                row.get(
                    key,
                    0,
                )
            ),
        }

    @staticmethod
    def _get_rate_record(
        table: list[dict],
        value_key: str,
        divisor_key: str,
    ) -> dict | None:
        candidates = [
            row
            for row in table
            if int(
                row.get(
                    divisor_key,
                    0,
                )
            ) > 0
        ]

        if not candidates:
            return None

        def calculate_rate(
            row: dict,
        ) -> float:
            value = float(
                row.get(
                    value_key,
                    0,
                )
            )

            divisor = float(
                row.get(
                    divisor_key,
                    0,
                )
            )

            if divisor <= 0:
                return 0.0

            return (
                value
                / divisor
            )

        row = max(
            candidates,
            key=lambda item: (
                calculate_rate(
                    item
                ),
                int(
                    item.get(
                        value_key,
                        0,
                    )
                ),
                int(
                    item.get(
                        "goal_difference",
                        0,
                    )
                ),
            ),
        )

        return {
            "team_id": int(
                row[
                    "team_id"
                ]
            ),
            "team_name": str(
                row[
                    "team_name"
                ]
            ),
            "played": int(
                row.get(
                    divisor_key,
                    0,
                )
            ),
            "value": round(
                calculate_rate(
                    row
                ),
                2,
            ),
        }

    def _get_clean_sheet_statistics(
        self,
        competition_id: int,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name,
                teams.short_name
            FROM competition_teams

            INNER JOIN teams
                ON teams.team_id =
                    competition_teams.team_id

            WHERE
                competition_teams.competition_id = ?

            ORDER BY
                teams.name
            """,
            (
                competition_id,
            ),
        )

        statistics: dict[int, dict] = {}

        for (
            team_id,
            team_name,
            short_name,
        ) in self.cursor.fetchall():
            statistics[
                int(
                    team_id
                )
            ] = {
                "team_id": int(
                    team_id
                ),
                "team_name": (
                    short_name
                    or team_name
                ),
                "played": 0,
                "clean_sheets": 0,
            }

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
            """,
            (
                competition_id,
            ),
        )

        for (
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
        ) in self.cursor.fetchall():
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

            home = statistics.get(
                home_team_id
            )

            away = statistics.get(
                away_team_id
            )

            if home is not None:
                home[
                    "played"
                ] += 1

                if away_goals == 0:
                    home[
                        "clean_sheets"
                    ] += 1

            if away is not None:
                away[
                    "played"
                ] += 1

                if home_goals == 0:
                    away[
                        "clean_sheets"
                    ] += 1

        return list(
            statistics.values()
        )

    @staticmethod
    def _get_clean_sheet_record(
        statistics: list[dict],
        key: str,
        highest: bool,
    ) -> dict | None:
        candidates = [
            row
            for row in statistics
            if int(
                row[
                    "played"
                ]
            ) > 0
        ]

        if not candidates:
            return None

        selector = (
            max
            if highest
            else min
        )

        row = selector(
            candidates,
            key=lambda item: (
                int(
                    item[
                        key
                    ]
                ),
                int(
                    item[
                        "played"
                    ]
                ),
            ),
        )

        return {
            "team_id": int(
                row[
                    "team_id"
                ]
            ),
            "team_name": str(
                row[
                    "team_name"
                ]
            ),
            "played": int(
                row[
                    "played"
                ]
            ),
            "value": int(
                row[
                    key
                ]
            ),
        }

    @staticmethod
    def _get_clean_sheet_rate_record(
        statistics: list[dict],
    ) -> dict | None:
        candidates = [
            row
            for row in statistics
            if int(
                row[
                    "played"
                ]
            ) > 0
        ]

        if not candidates:
            return None

        def clean_sheet_rate(
            row: dict,
        ) -> float:
            return (
                int(
                    row[
                        "clean_sheets"
                    ]
                )
                / int(
                    row[
                        "played"
                    ]
                )
                * 100
            )

        row = max(
            candidates,
            key=lambda item: (
                clean_sheet_rate(
                    item
                ),
                int(
                    item[
                        "clean_sheets"
                    ]
                ),
            ),
        )

        return {
            "team_id": int(
                row[
                    "team_id"
                ]
            ),
            "team_name": str(
                row[
                    "team_name"
                ]
            ),
            "played": int(
                row[
                    "played"
                ]
            ),
            "clean_sheets": int(
                row[
                    "clean_sheets"
                ]
            ),
            "value": round(
                clean_sheet_rate(
                    row
                ),
                1,
            ),
        }