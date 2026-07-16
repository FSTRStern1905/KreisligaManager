import sqlite3


class TableService:
    VALID_MODES = {
        "all",
        "home",
        "away",
    }

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_table(
        self,
        competition_id: int,
        mode: str = "all",
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Ungültiger Tabellenmodus: {mode}"
            )

        standings = self._create_empty_table(
            competition_id
        )

        matches = self._load_finished_matches(
            competition_id
        )

        for match in matches:
            self._apply_match_result(
                standings=standings,
                match=match,
                mode=mode,
            )

        self._calculate_goal_differences(
            standings
        )

        return self._sort_table(
            standings
        )

    def _create_empty_table(
        self,
        competition_id: int,
    ) -> dict[int, dict]:
        teams = self._load_competition_teams(
            competition_id
        )

        standings: dict[int, dict] = {}

        for (
            team_id,
            team_name,
            short_name,
        ) in teams:
            standings[team_id] = {
                "team_id": team_id,
                "team_name": (
                    short_name or team_name
                ),
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
            }

        return standings

    def _apply_match_result(
        self,
        standings: dict[int, dict],
        match: tuple,
        mode: str,
    ):
        (
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
        ) = match

        if home_team_id not in standings:
            return

        if away_team_id not in standings:
            return

        if mode in {
            "all",
            "home",
        }:
            self._apply_team_result(
                team=standings[home_team_id],
                goals_for=home_goals,
                goals_against=away_goals,
            )

        if mode in {
            "all",
            "away",
        }:
            self._apply_team_result(
                team=standings[away_team_id],
                goals_for=away_goals,
                goals_against=home_goals,
            )

    def _apply_team_result(
        self,
        team: dict,
        goals_for: int,
        goals_against: int,
    ):
        team["played"] += 1
        team["goals_for"] += goals_for
        team["goals_against"] += goals_against

        if goals_for > goals_against:
            team["wins"] += 1
            team["points"] += 3

        elif goals_for < goals_against:
            team["losses"] += 1

        else:
            team["draws"] += 1
            team["points"] += 1

    def _calculate_goal_differences(
        self,
        standings: dict[int, dict],
    ):
        for team in standings.values():
            team["goal_difference"] = (
                team["goals_for"]
                - team["goals_against"]
            )

    def _sort_table(
        self,
        standings: dict[int, dict],
    ) -> list[dict]:
        table = list(
            standings.values()
        )

        table.sort(
            key=lambda team: (
                -team["points"],
                -team["goal_difference"],
                -team["goals_for"],
                team["team_name"].lower(),
            )
        )

        return table

    def _load_competition_teams(
        self,
        competition_id: int,
    ) -> list[tuple]:
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
            (competition_id,),
        )

        return self.cursor.fetchall()

    def _load_finished_matches(
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
            (competition_id,),
        )

        return self.cursor.fetchall()