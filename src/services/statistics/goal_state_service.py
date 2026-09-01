from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class GoalStateService:
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

        result: list[dict] = []

        for team in teams.values():
            result.append(
                self._finalize_team(
                    team
                )
            )

        result.sort(
            key=lambda team: (
                -float(
                    team[
                        "goal_while_trailing_percentage"
                    ]
                ),
                -int(
                    team[
                        "goals_while_trailing"
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

                "goals_while_level": 0,
                "goals_while_leading": 0,
                "goals_while_trailing": 0,

                "conceded_while_level": 0,
                "conceded_while_leading": 0,
                "conceded_while_trailing": 0,

                "matches_trailing": 0,

                "equalized_after_trailing": 0,

                "next_goal_after_trailing_own": 0,
                "next_goal_after_trailing_opponent": 0,

                "equalizer_response_minutes_total": 0,
                "equalizer_response_count": 0,
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

        events = self._load_goal_events(
            match_id
        )

        if not events:
            return

        home_score = 0
        away_score = 0

        trailing_data = {
            home_team_id: {
                "first_trailing_minute": None,
                "next_goal_checked": False,
                "equalized": False,
            },
            away_team_id: {
                "first_trailing_minute": None,
                "next_goal_checked": False,
                "equalized": False,
            },
        }

        for event in events:
            minute = self._normalize_minute(
                event["minute"]
            )

            if minute is None:
                continue

            event_team_id = event[
                "team_id"
            ]

            if event_team_id is None:
                continue

            scoring_team_id = int(
                event_team_id
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
                continue

            home_state_before = (
                self._get_state(
                    goals_for=home_score,
                    goals_against=away_score,
                )
            )

            away_state_before = (
                self._get_state(
                    goals_for=away_score,
                    goals_against=home_score,
                )
            )

            if scoring_team_id == home_team_id:
                scoring_state = (
                    home_state_before
                )

                conceding_state = (
                    away_state_before
                )

            else:
                scoring_state = (
                    away_state_before
                )

                conceding_state = (
                    home_state_before
                )

            self._register_scored_goal(
                team=teams[
                    scoring_team_id
                ],
                state=scoring_state,
            )

            self._register_conceded_goal(
                team=teams[
                    conceding_team_id
                ],
                state=conceding_state,
            )

            self._check_next_goal_after_trailing(
                trailing_data=trailing_data,
                scoring_team_id=scoring_team_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                teams=teams,
            )

            if scoring_team_id == home_team_id:
                home_score += 1
            else:
                away_score += 1

            self._update_trailing_state(
                team_id=home_team_id,
                goals_for=home_score,
                goals_against=away_score,
                minute=minute,
                trailing_data=trailing_data,
                teams=teams,
            )

            self._update_trailing_state(
                team_id=away_team_id,
                goals_for=away_score,
                goals_against=home_score,
                minute=minute,
                trailing_data=trailing_data,
                teams=teams,
            )

    @staticmethod
    def _get_state(
        goals_for: int,
        goals_against: int,
    ) -> str:
        if goals_for > goals_against:
            return "leading"

        if goals_for < goals_against:
            return "trailing"

        return "level"

    @staticmethod
    def _register_scored_goal(
        team: dict,
        state: str,
    ) -> None:
        if state == "leading":
            team[
                "goals_while_leading"
            ] += 1

        elif state == "trailing":
            team[
                "goals_while_trailing"
            ] += 1

        else:
            team[
                "goals_while_level"
            ] += 1

    @staticmethod
    def _register_conceded_goal(
        team: dict,
        state: str,
    ) -> None:
        if state == "leading":
            team[
                "conceded_while_leading"
            ] += 1

        elif state == "trailing":
            team[
                "conceded_while_trailing"
            ] += 1

        else:
            team[
                "conceded_while_level"
            ] += 1

    @staticmethod
    def _check_next_goal_after_trailing(
        trailing_data: dict[int, dict],
        scoring_team_id: int,
        home_team_id: int,
        away_team_id: int,
        teams: dict[int, dict],
    ) -> None:
        for team_id in (
            home_team_id,
            away_team_id,
        ):
            data = trailing_data[
                team_id
            ]

            if (
                data[
                    "first_trailing_minute"
                ]
                is None
            ):
                continue

            if data[
                "next_goal_checked"
            ]:
                continue

            if scoring_team_id == team_id:
                teams[
                    team_id
                ][
                    "next_goal_after_trailing_own"
                ] += 1

            else:
                teams[
                    team_id
                ][
                    "next_goal_after_trailing_opponent"
                ] += 1

            data[
                "next_goal_checked"
            ] = True

    @staticmethod
    def _update_trailing_state(
        team_id: int,
        goals_for: int,
        goals_against: int,
        minute: int,
        trailing_data: dict[int, dict],
        teams: dict[int, dict],
    ) -> None:
        data = trailing_data[
            team_id
        ]

        is_trailing = (
            goals_for
            < goals_against
        )

        is_level = (
            goals_for
            == goals_against
        )

        if (
            is_trailing
            and data[
                "first_trailing_minute"
            ]
            is None
        ):
            data[
                "first_trailing_minute"
            ] = minute

            teams[
                team_id
            ][
                "matches_trailing"
            ] += 1

            return

        if (
            is_level
            and data[
                "first_trailing_minute"
            ]
            is not None
            and not data[
                "equalized"
            ]
        ):
            trailing_minute = int(
                data[
                    "first_trailing_minute"
                ]
            )

            response_minutes = max(
                0,
                minute
                - trailing_minute,
            )

            teams[
                team_id
            ][
                "equalized_after_trailing"
            ] += 1

            teams[
                team_id
            ][
                "equalizer_response_minutes_total"
            ] += response_minutes

            teams[
                team_id
            ][
                "equalizer_response_count"
            ] += 1

            data[
                "equalized"
            ] = True

    def _finalize_team(
        self,
        team: dict,
    ) -> dict:
        goals_while_level = int(
            team[
                "goals_while_level"
            ]
        )

        goals_while_leading = int(
            team[
                "goals_while_leading"
            ]
        )

        goals_while_trailing = int(
            team[
                "goals_while_trailing"
            ]
        )

        total_goals = (
            goals_while_level
            + goals_while_leading
            + goals_while_trailing
        )

        matches_trailing = int(
            team[
                "matches_trailing"
            ]
        )

        equalized_after_trailing = int(
            team[
                "equalized_after_trailing"
            ]
        )

        response_count = int(
            team[
                "equalizer_response_count"
            ]
        )

        response_minutes_total = int(
            team[
                "equalizer_response_minutes_total"
            ]
        )

        if response_count > 0:
            average_equalizer_minutes = round(
                response_minutes_total
                / response_count,
                1,
            )
        else:
            average_equalizer_minutes = 0.0

        return {
            **team,

            "total_goals": total_goals,

            "goal_while_level_percentage": (
                self._percentage(
                    goals_while_level,
                    total_goals,
                )
            ),

            "goal_while_leading_percentage": (
                self._percentage(
                    goals_while_leading,
                    total_goals,
                )
            ),

            "goal_while_trailing_percentage": (
                self._percentage(
                    goals_while_trailing,
                    total_goals,
                )
            ),

            "equalizer_percentage": (
                self._percentage(
                    equalized_after_trailing,
                    matches_trailing,
                )
            ),

            "average_equalizer_minutes": (
                average_equalizer_minutes
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
                away_team_id
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
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