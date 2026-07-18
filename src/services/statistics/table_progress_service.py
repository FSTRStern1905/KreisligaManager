import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class TableProgressService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
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

        matches_by_matchday = (
            self._load_matches_by_matchday(
                competition_id
            )
        )

        for matchday in sorted(
            matches_by_matchday
        ):
            current_table = self._calculate_table_until_matchday(
                competition_id=competition_id,
                matchday=matchday,
            )

            for position, table_row in enumerate(
                current_table,
                start=1,
            ):
                team_id = table_row["team_id"]

                if team_id not in teams:
                    continue

                teams[team_id]["positions"].append(
                    {
                        "matchday": matchday,
                        "position": position,
                    }
                )

        result = list(
            teams.values()
        )

        result.sort(
            key=lambda team: (
                team["team_name"].lower()
            )
        )

        return result

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
            ORDER BY
                matchday
            """,
            (competition_id,),
        )

        return [
            row[0]
            for row in self.cursor.fetchall()
        ]

    def _create_team_progress(
        self,
        competition_id: int,
    ) -> dict[int, dict]:
        table = self.table_service.get_table(
            competition_id=competition_id,
            mode="all",
        )

        teams = {}

        for team in table:
            teams[team["team_id"]] = {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "positions": [],
            }

        return teams

    def _load_matches_by_matchday(
        self,
        competition_id: int,
    ) -> dict[int, list[sqlite3.Row]]:
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
                AND matchday IS NOT NULL
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday,
                match_id
            """,
            (competition_id,),
        )

        matches = {}

        for row in self.cursor.fetchall():
            matchday = row[1]

            matches.setdefault(
                matchday,
                [],
            ).append(row)

        return matches

    def _calculate_table_until_matchday(
        self,
        competition_id: int,
        matchday: int,
    ) -> list[dict]:
        standings = self.table_service._create_empty_table(
            competition_id
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
                matchday,
                match_id
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