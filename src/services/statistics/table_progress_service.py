from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class TableProgressService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.table_service = TableService(
            connection
        )

    def get_table_progress(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        teams = self._create_team_progress(
            competition_id
        )

        matchdays = self.get_matchdays(
            competition_id
        )

        for matchday in matchdays:
            current_table = (
                self._calculate_table_until_matchday(
                    competition_id=competition_id,
                    matchday=matchday,
                )
            )

            for position, table_row in enumerate(
                current_table,
                start=1,
            ):
                team_id = int(
                    table_row["team_id"]
                )

                if team_id not in teams:
                    continue

                teams[
                    team_id
                ]["progress"].append(
                    {
                        "matchday": matchday,
                        "position": position,
                        "points": int(
                            table_row["points"]
                        ),
                        "played": int(
                            table_row["played"]
                        ),
                        "wins": int(
                            table_row["wins"]
                        ),
                        "draws": int(
                            table_row["draws"]
                        ),
                        "losses": int(
                            table_row["losses"]
                        ),
                        "goals_for": int(
                            table_row["goals_for"]
                        ),
                        "goals_against": int(
                            table_row["goals_against"]
                        ),
                        "goal_difference": int(
                            table_row[
                                "goal_difference"
                            ]
                        ),
                    }
                )

        result = list(
            teams.values()
        )

        for team in result:
            progress = self._filter_progress_by_played_games(
                team["progress"]
            )

            team["progress"] = progress

            team["positions"] = [
                {
                    "played": row[
                        "played"
                    ],
                    "matchday": row[
                        "matchday"
                    ],
                    "position": row[
                        "position"
                    ],
                }
                for row in progress
            ]

            team["points_progress"] = [
                {
                    "played": row[
                        "played"
                    ],
                    "matchday": row[
                        "matchday"
                    ],
                    "points": row[
                        "points"
                    ],
                }
                for row in progress
            ]

            if progress:
                latest = progress[
                    -1
                ]

                team["current_position"] = (
                    latest["position"]
                )

                team["current_points"] = (
                    latest["points"]
                )

                team["current_matchday"] = (
                    latest["matchday"]
                )

                team["current_played"] = (
                    latest["played"]
                )

            else:
                team["current_position"] = None
                team["current_points"] = 0
                team["current_matchday"] = None
                team["current_played"] = 0

        result.sort(
            key=lambda team: (
                (
                    team["current_position"]
                    if team[
                        "current_position"
                    ] is not None
                    else 9999
                ),
                team[
                    "team_name"
                ].lower(),
            )
        )

        return result


    @staticmethod
    def _filter_progress_by_played_games(
        progress: list[dict],
    ) -> list[dict]:
        filtered: list[dict] = []
        seen_played: set[int] = set()

        for row in progress:
            played = int(
                row.get(
                    "played",
                    0,
                )
            )

            if played <= 0:
                continue

            if played in seen_played:
                continue

            seen_played.add(
                played
            )

            filtered.append(
                row
            )

        return filtered

    def get_team_progress(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict | None:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        progress = self.get_table_progress(
            competition_id
        )

        for team in progress:
            if int(
                team["team_id"]
            ) == team_id:
                return team

        return None

    def get_matchdays(
        self,
        competition_id: int,
    ) -> list[int]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        self.cursor.execute(
            """
            SELECT DISTINCT
                matchday

            FROM matches

            WHERE
                competition_id = ?
                AND status = 'finished'
                AND matchday IS NOT NULL
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL

            ORDER BY
                matchday
            """,
            (competition_id,),
        )

        return [
            int(
                row[0]
            )
            for row in self.cursor.fetchall()
            if row[0] is not None
        ]

    def _create_team_progress(
        self,
        competition_id: int,
    ) -> dict[int, dict]:
        table = self.table_service.get_table(
            competition_id=competition_id,
            mode="all",
        )

        teams: dict[
            int,
            dict,
        ] = {}

        for team in table:
            team_id = int(
                team["team_id"]
            )

            teams[
                team_id
            ] = {
                "team_id": team_id,
                "team_name": team[
                    "team_name"
                ],
                "progress": [],
                "positions": [],
                "points_progress": [],
                "current_position": None,
                "current_points": 0,
                "current_matchday": None,
                "current_played": 0,
            }

        return teams

    def _calculate_table_until_matchday(
        self,
        competition_id: int,
        matchday: int,
    ) -> list[dict]:
        standings = (
            self.table_service._create_empty_table(
                competition_id
            )
        )

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
                AND matchday IS NOT NULL
                AND matchday <= ?
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL

            ORDER BY
                matchday ASC,
                match_date ASC,
                match_id ASC
            """,
            (
                competition_id,
                matchday,
            ),
        )

        for match in self.cursor.fetchall():
            self.table_service._apply_match_result(
                standings=standings,
                match=match,
                mode="all",
            )

        self.table_service._calculate_goal_differences(
            standings
        )

        return self.table_service._sort_table(
            standings
        )