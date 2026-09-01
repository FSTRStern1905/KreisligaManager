from __future__ import annotations

import sqlite3

from src.services.statistics.table_service import (
    TableService,
)


class TeamGoalPhaseService:
    EARLY_MINUTE_MAX = 15
    LATE_MINUTE_MIN = 76

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
                "total_goals": int(
                    team["goals_for"]
                ),
                "total_goals_against": int(
                    team["goals_against"]
                ),
                "early_goals": 0,
                "early_goals_against": 0,
                "late_goals": 0,
                "late_goals_against": 0,
            }

        events = self._load_goal_events(
            competition_id
        )

        for event in events:
            (
                event_id,
                minute,
                event_code,
                event_team_id,
                home_team_id,
                away_team_id,
            ) = event

            normalized_minute = (
                self._normalize_minute(
                    minute
                )
            )

            if normalized_minute is None:
                continue

            if event_team_id is None:
                continue

            scoring_team_id = int(
                event_team_id
            )

            home_team_id = int(
                home_team_id
            )

            away_team_id = int(
                away_team_id
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

            if (
                scoring_team_id not in teams
                or conceding_team_id not in teams
            ):
                continue

            if (
                normalized_minute
                <= self.EARLY_MINUTE_MAX
            ):
                teams[
                    scoring_team_id
                ][
                    "early_goals"
                ] += 1

                teams[
                    conceding_team_id
                ][
                    "early_goals_against"
                ] += 1

            if (
                normalized_minute
                >= self.LATE_MINUTE_MIN
            ):
                teams[
                    scoring_team_id
                ][
                    "late_goals"
                ] += 1

                teams[
                    conceding_team_id
                ][
                    "late_goals_against"
                ] += 1

        result: list[dict] = []

        for team in teams.values():
            total_goals = int(
                team["total_goals"]
            )

            total_goals_against = int(
                team["total_goals_against"]
            )

            early_goals = int(
                team["early_goals"]
            )

            early_goals_against = int(
                team["early_goals_against"]
            )

            late_goals = int(
                team["late_goals"]
            )

            late_goals_against = int(
                team["late_goals_against"]
            )

            result.append(
                {
                    **team,
                    "early_goal_percentage": (
                        self._percentage(
                            early_goals,
                            total_goals,
                        )
                    ),
                    "early_conceded_percentage": (
                        self._percentage(
                            early_goals_against,
                            total_goals_against,
                        )
                    ),
                    "late_goal_percentage": (
                        self._percentage(
                            late_goals,
                            total_goals,
                        )
                    ),
                    "late_conceded_percentage": (
                        self._percentage(
                            late_goals_against,
                            total_goals_against,
                        )
                    ),
                    "late_balance": (
                        late_goals
                        - late_goals_against
                    ),
                }
            )

        result.sort(
            key=lambda team: (
                -float(
                    team[
                        "late_goal_percentage"
                    ]
                ),
                -int(
                    team[
                        "late_goals"
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

    def _load_goal_events(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                events.event_id,
                events.minute,
                event_types.code,
                events.team_id,
                matches.home_team_id,
                matches.away_team_id
            FROM events

            INNER JOIN event_types
                ON event_types.event_type_id =
                    events.event_type_id

            INNER JOIN matches
                ON matches.match_id =
                    events.match_id

            WHERE
                matches.competition_id = ?
                AND matches.status = 'finished'
                AND events.minute IS NOT NULL
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL',
                    'OWN_GOAL'
                )

            ORDER BY
                matches.matchday,
                events.match_id,
                events.minute,
                events.event_id
            """,
            (
                competition_id,
            ),
        )

        return self.cursor.fetchall()

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