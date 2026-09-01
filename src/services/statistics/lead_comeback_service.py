from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class LeadComebackService:
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

        result = []

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
                        "points_after_trailing"
                    ]
                ),
                -float(
                    team[
                        "comeback_percentage"
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

                "matches_trailing": 0,
                "wins_after_trailing": 0,
                "draws_after_trailing": 0,
                "losses_after_trailing": 0,

                "matches_leading": 0,
                "wins_after_leading": 0,
                "draws_after_leading": 0,
                "losses_after_leading": 0,
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
            return

        goal_events = self._load_goal_events(
            match_id
        )

        if not goal_events:
            return

        current_home_goals = 0
        current_away_goals = 0

        home_led = False
        away_led = False

        home_trailed = False
        away_trailed = False

        for event in goal_events:
            scoring_team_id = event[
                "team_id"
            ]

            if scoring_team_id is None:
                continue

            scoring_team_id = int(
                scoring_team_id
            )

            if scoring_team_id == home_team_id:
                current_home_goals += 1

            elif scoring_team_id == away_team_id:
                current_away_goals += 1

            else:
                continue

            if (
                current_home_goals
                > current_away_goals
            ):
                home_led = True
                away_trailed = True

            elif (
                current_away_goals
                > current_home_goals
            ):
                away_led = True
                home_trailed = True

        self._apply_team_result(
            team=teams[
                home_team_id
            ],
            led=home_led,
            trailed=home_trailed,
            goals_for=home_goals,
            goals_against=away_goals,
        )

        self._apply_team_result(
            team=teams[
                away_team_id
            ],
            led=away_led,
            trailed=away_trailed,
            goals_for=away_goals,
            goals_against=home_goals,
        )

    @staticmethod
    def _apply_team_result(
        team: dict,
        led: bool,
        trailed: bool,
        goals_for: int,
        goals_against: int,
    ) -> None:
        won = (
            goals_for
            > goals_against
        )

        drawn = (
            goals_for
            == goals_against
        )

        lost = (
            goals_for
            < goals_against
        )

        if trailed:
            team[
                "matches_trailing"
            ] += 1

            if won:
                team[
                    "wins_after_trailing"
                ] += 1

            elif drawn:
                team[
                    "draws_after_trailing"
                ] += 1

            elif lost:
                team[
                    "losses_after_trailing"
                ] += 1

        if led:
            team[
                "matches_leading"
            ] += 1

            if won:
                team[
                    "wins_after_leading"
                ] += 1

            elif drawn:
                team[
                    "draws_after_leading"
                ] += 1

            elif lost:
                team[
                    "losses_after_leading"
                ] += 1

    def _finalize_team(
        self,
        team: dict,
    ) -> dict:
        matches_trailing = int(
            team[
                "matches_trailing"
            ]
        )

        wins_after_trailing = int(
            team[
                "wins_after_trailing"
            ]
        )

        draws_after_trailing = int(
            team[
                "draws_after_trailing"
            ]
        )

        matches_leading = int(
            team[
                "matches_leading"
            ]
        )

        wins_after_leading = int(
            team[
                "wins_after_leading"
            ]
        )

        draws_after_leading = int(
            team[
                "draws_after_leading"
            ]
        )

        losses_after_leading = int(
            team[
                "losses_after_leading"
            ]
        )

        points_after_trailing = (
            wins_after_trailing * 3
            + draws_after_trailing
        )

        comeback_matches = (
            wins_after_trailing
            + draws_after_trailing
        )

        comeback_percentage = (
            self._percentage(
                comeback_matches,
                matches_trailing,
            )
        )

        lead_win_percentage = (
            self._percentage(
                wins_after_leading,
                matches_leading,
            )
        )

        dropped_points_after_leading = (
            draws_after_leading * 2
            + losses_after_leading * 3
        )

        return {
            **team,

            "points_after_trailing": (
                points_after_trailing
            ),

            "comeback_matches": (
                comeback_matches
            ),

            "comeback_percentage": (
                comeback_percentage
            ),

            "lead_win_percentage": (
                lead_win_percentage
            ),

            "dropped_points_after_leading": (
                dropped_points_after_leading
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

        return [
            dict(
                row
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

        return [
            dict(
                row
            )
            for row in self.cursor.fetchall()
        ]

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