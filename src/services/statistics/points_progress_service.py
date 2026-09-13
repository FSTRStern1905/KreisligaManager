import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class PointsProgressService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()
        self.table_service = TableService(connection)

    def get_points_progress(
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

        matches = self._load_finished_matches(
            competition_id
        )

        if not matches:
            return list(teams.values())

        for match in matches:
            affected_team_ids = (
                match["home_team_id"],
                match["away_team_id"],
            )

            self._apply_match_points(
                teams=teams,
                match=match,
            )

            for team_id in affected_team_ids:
                if team_id not in teams:
                    continue

                team = teams[team_id]

                team["progress"].append(
                    {
                        "match_number": team["played"],
                        "matchday": match["matchday"],
                        "points": team["points"],
                        "played": team["played"],
                    }
                )

        result = list(
            teams.values()
        )

        result.sort(
            key=lambda team: (
                -team["points"],
                team["team_name"].lower(),
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
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
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
        standings = (
            self.table_service._create_empty_table(
                competition_id
            )
        )

        teams: dict[int, dict] = {}

        for team_id, team in standings.items():
            teams[team_id] = {
                "team_id": team_id,
                "team_name": team["team_name"],
                "played": 0,
                "points": 0,
                "progress": [
                    {
                        "match_number": 0,
                        "matchday": 0,
                        "points": 0,
                        "played": 0,
                    }
                ],
            }

        return teams

    def _apply_match_points(
        self,
        teams: dict[int, dict],
        match: dict,
    ):
        home_team_id = match["home_team_id"]
        away_team_id = match["away_team_id"]
        home_goals = match["home_goals"]
        away_goals = match["away_goals"]

        if home_team_id not in teams:
            return

        if away_team_id not in teams:
            return

        home_team = teams[home_team_id]
        away_team = teams[away_team_id]

        home_team["played"] += 1
        away_team["played"] += 1

        if home_goals > away_goals:
            home_team["points"] += 3

        elif home_goals < away_goals:
            away_team["points"] += 3

        else:
            home_team["points"] += 1
            away_team["points"] += 1

    def _load_finished_matches(
        self,
        competition_id: int,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                match_id,
                matchday,
                match_date,
                kickoff_time,
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
                CASE
                    WHEN match_date IS NULL
                         OR match_date = ''
                    THEN 1
                    ELSE 0
                END,
                match_date,
                kickoff_time,
                matchday,
                match_id
            """,
            (competition_id,),
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
