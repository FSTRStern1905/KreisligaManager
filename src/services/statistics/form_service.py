import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class FormService(TableService):
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        super().__init__(connection)

    def get_form_table(
        self,
        competition_id: int,
        matches: int = 5,
    ) -> list[dict]:
        standings = self._create_empty_table(
            competition_id
        )

        recent_matches = (
            self._load_recent_matches(
                competition_id,
                matches,
            )
        )

        for match in recent_matches:
            self._apply_match_result(
                standings=standings,
                match=match,
                mode="all",
            )

        self._calculate_goal_differences(
            standings
        )

        return self._sort_table(
            standings
        )

    def _load_recent_matches(
        self,
        competition_id: int,
        match_count: int,
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
                matchday DESC,
                match_id DESC
            """,
            (competition_id,),
        )

        matches = self.cursor.fetchall()

        team_matches = {}
        result = []

        for match in matches:
            home_team = match[0]
            away_team = match[1]

            home_count = team_matches.get(
                home_team,
                0,
            )

            away_count = team_matches.get(
                away_team,
                0,
            )

            if (
                home_count >= match_count
                and away_count >= match_count
            ):
                continue

            result.append(match)

            if home_count < match_count:
                team_matches[home_team] = (
                    home_count + 1
                )

            if away_count < match_count:
                team_matches[away_team] = (
                    away_count + 1
                )

        result.reverse()

        return result