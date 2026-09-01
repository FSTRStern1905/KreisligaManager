from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class OpeningGoalService:
    GOAL_EVENT_CODES = (
        "GOAL",
        "PENALTY_GOAL",
        "OWN_GOAL",
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

        teams = self._create_team_statistics(
            table
        )

        matches = self._load_matches(
            competition_id
        )

        for match in matches:
            self._analyse_match(
                match=match,
                teams=teams,
            )

        result = [
            self._finalize_team(
                team
            )
            for team in teams.values()
        ]

        result.sort(
            key=lambda team: (
                -float(
                    team[
                        "win_percentage_after_scoring_first"
                    ]
                ),
                -int(
                    team[
                        "scored_first"
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

    def _create_team_statistics(
        self,
        table: list[dict],
    ) -> dict[int, dict]:
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

                "scored_first": 0,
                "won_after_scoring_first": 0,
                "drawn_after_scoring_first": 0,
                "lost_after_scoring_first": 0,

                "conceded_first": 0,
                "won_after_conceding_first": 0,
                "drawn_after_conceding_first": 0,
                "lost_after_conceding_first": 0,

                "opening_goal_minute_total": 0,
                "opening_goal_minute_count": 0,

                "opening_conceded_minute_total": 0,
                "opening_conceded_minute_count": 0,

                "scoreless_draws": 0,
            }

        return teams

    def _analyse_match(
        self,
        match: dict,
        teams: dict[int, dict],
    ) -> None:
        match_id = int(
            match["match_id"]
        )

        home_team_id = int(
            match["home_team_id"]
        )

        away_team_id = int(
            match["away_team_id"]
        )

        if (
            home_team_id not in teams
            or away_team_id not in teams
        ):
            return

        home_goals = int(
            match["home_goals"]
        )

        away_goals = int(
            match["away_goals"]
        )

        events = self._load_goal_events(
            match_id
        )

        if not events:
            if (
                home_goals == 0
                and away_goals == 0
            ):
                teams[
                    home_team_id
                ][
                    "scoreless_draws"
                ] += 1

                teams[
                    away_team_id
                ][
                    "scoreless_draws"
                ] += 1

            return

        first_goal = events[0]

        scoring_team_id_raw = (
            first_goal["team_id"]
        )

        if scoring_team_id_raw is None:
            return

        scoring_team_id = int(
            scoring_team_id_raw
        )

        if scoring_team_id == home_team_id:
            conceding_team_id = (
                away_team_id
            )

        elif scoring_team_id == away_team_id:
            conceding_team_id = (
                home_team_id
            )

        else:
            return

        minute = self._normalize_minute(
            first_goal["minute"]
        )

        teams[
            scoring_team_id
        ][
            "scored_first"
        ] += 1

        teams[
            conceding_team_id
        ][
            "conceded_first"
        ] += 1

        if minute is not None:
            teams[
                scoring_team_id
            ][
                "opening_goal_minute_total"
            ] += minute

            teams[
                scoring_team_id
            ][
                "opening_goal_minute_count"
            ] += 1

            teams[
                conceding_team_id
            ][
                "opening_conceded_minute_total"
            ] += minute

            teams[
                conceding_team_id
            ][
                "opening_conceded_minute_count"
            ] += 1

        scoring_team_result = (
            self._get_team_result(
                team_id=scoring_team_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_goals=home_goals,
                away_goals=away_goals,
            )
        )

        conceding_team_result = (
            self._get_team_result(
                team_id=conceding_team_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_goals=home_goals,
                away_goals=away_goals,
            )
        )

        self._register_result_after_scoring_first(
            team=teams[
                scoring_team_id
            ],
            result=scoring_team_result,
        )

        self._register_result_after_conceding_first(
            team=teams[
                conceding_team_id
            ],
            result=conceding_team_result,
        )

    @staticmethod
    def _get_team_result(
        team_id: int,
        home_team_id: int,
        away_team_id: int,
        home_goals: int,
        away_goals: int,
    ) -> str:
        if team_id == home_team_id:
            goals_for = home_goals
            goals_against = away_goals

        elif team_id == away_team_id:
            goals_for = away_goals
            goals_against = home_goals

        else:
            raise ValueError(
                "Mannschaft gehört nicht zum Spiel."
            )

        if goals_for > goals_against:
            return "win"

        if goals_for < goals_against:
            return "loss"

        return "draw"

    @staticmethod
    def _register_result_after_scoring_first(
        team: dict,
        result: str,
    ) -> None:
        if result == "win":
            team[
                "won_after_scoring_first"
            ] += 1

        elif result == "draw":
            team[
                "drawn_after_scoring_first"
            ] += 1

        elif result == "loss":
            team[
                "lost_after_scoring_first"
            ] += 1

    @staticmethod
    def _register_result_after_conceding_first(
        team: dict,
        result: str,
    ) -> None:
        if result == "win":
            team[
                "won_after_conceding_first"
            ] += 1

        elif result == "draw":
            team[
                "drawn_after_conceding_first"
            ] += 1

        elif result == "loss":
            team[
                "lost_after_conceding_first"
            ] += 1

    def _finalize_team(
        self,
        team: dict,
    ) -> dict:
        scored_first = int(
            team["scored_first"]
        )

        conceded_first = int(
            team["conceded_first"]
        )

        won_after_scoring_first = int(
            team[
                "won_after_scoring_first"
            ]
        )

        drawn_after_scoring_first = int(
            team[
                "drawn_after_scoring_first"
            ]
        )

        lost_after_scoring_first = int(
            team[
                "lost_after_scoring_first"
            ]
        )

        won_after_conceding_first = int(
            team[
                "won_after_conceding_first"
            ]
        )

        drawn_after_conceding_first = int(
            team[
                "drawn_after_conceding_first"
            ]
        )

        lost_after_conceding_first = int(
            team[
                "lost_after_conceding_first"
            ]
        )

        points_after_scoring_first = (
            won_after_scoring_first * 3
            + drawn_after_scoring_first
        )

        points_after_conceding_first = (
            won_after_conceding_first * 3
            + drawn_after_conceding_first
        )

        maximum_points_after_scoring_first = (
            scored_first * 3
        )

        maximum_points_after_conceding_first = (
            conceded_first * 3
        )

        average_opening_goal_minute = (
            self._average(
                total=int(
                    team[
                        "opening_goal_minute_total"
                    ]
                ),
                count=int(
                    team[
                        "opening_goal_minute_count"
                    ]
                ),
            )
        )

        average_opening_conceded_minute = (
            self._average(
                total=int(
                    team[
                        "opening_conceded_minute_total"
                    ]
                ),
                count=int(
                    team[
                        "opening_conceded_minute_count"
                    ]
                ),
            )
        )

        return {
            **team,

            "win_percentage_after_scoring_first": (
                self._percentage(
                    won_after_scoring_first,
                    scored_first,
                )
            ),

            "draw_percentage_after_scoring_first": (
                self._percentage(
                    drawn_after_scoring_first,
                    scored_first,
                )
            ),

            "loss_percentage_after_scoring_first": (
                self._percentage(
                    lost_after_scoring_first,
                    scored_first,
                )
            ),

            "points_after_scoring_first": (
                points_after_scoring_first
            ),

            "points_percentage_after_scoring_first": (
                self._percentage(
                    points_after_scoring_first,
                    maximum_points_after_scoring_first,
                )
            ),

            "average_opening_goal_minute": (
                average_opening_goal_minute
            ),

            "win_percentage_after_conceding_first": (
                self._percentage(
                    won_after_conceding_first,
                    conceded_first,
                )
            ),

            "draw_percentage_after_conceding_first": (
                self._percentage(
                    drawn_after_conceding_first,
                    conceded_first,
                )
            ),

            "loss_percentage_after_conceding_first": (
                self._percentage(
                    lost_after_conceding_first,
                    conceded_first,
                )
            ),

            "points_after_conceding_first": (
                points_after_conceding_first
            ),

            "points_percentage_after_conceding_first": (
                self._percentage(
                    points_after_conceding_first,
                    maximum_points_after_conceding_first,
                )
            ),

            "average_opening_conceded_minute": (
                average_opening_conceded_minute
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

    def _load_goal_events(
        self,
        match_id: int,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                events.event_id,
                events.minute,
                events.team_id,
                event_types.code
            FROM events

            INNER JOIN event_types
                ON event_types.event_type_id =
                    events.event_type_id

            WHERE
                events.match_id = ?
                AND events.minute IS NOT NULL
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL',
                    'OWN_GOAL'
                )

            ORDER BY
                events.minute,
                events.event_id
            """,
            (
                match_id,
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

    @staticmethod
    def _normalize_minute(
        minute,
    ) -> int | None:
        if minute is None:
            return None

        if isinstance(
            minute,
            int,
        ):
            return max(
                0,
                min(
                    minute,
                    90,
                ),
            )

        text = str(
            minute
        ).strip()

        if not text:
            return None

        if "+" in text:
            text = text.split(
                "+",
                1,
            )[0]

        try:
            value = int(
                text
            )

        except ValueError:
            return None

        return max(
            0,
            min(
                value,
                90,
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

    @staticmethod
    def _average(
        total: int,
        count: int,
    ) -> float:
        if count <= 0:
            return 0.0

        return round(
            total
            / count,
            1,
        )