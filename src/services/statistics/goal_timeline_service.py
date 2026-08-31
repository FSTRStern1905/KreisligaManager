from __future__ import annotations

import sqlite3


class GoalTimelineService:
    INTERVALS = (
        (0, 15),
        (16, 30),
        (31, 45),
        (46, 60),
        (61, 75),
        (76, 90),
    )

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

    def get_goal_timeline(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        intervals = self._create_intervals()

        goal_events = self._load_goal_events(
            competition_id
        )

        for event in goal_events:
            minute = self._normalize_minute(
                event["minute"]
            )

            if minute is None:
                continue

            interval = self._find_interval(
                minute=minute,
                intervals=intervals,
            )

            if interval is None:
                continue

            interval["goals"] += 1

            goal_side = self._get_goal_side(
                event
            )

            if goal_side == "home":
                interval["home_goals"] += 1

            elif goal_side == "away":
                interval["away_goals"] += 1

            else:
                interval["unassigned_goals"] += 1

        total_goals = sum(
            interval["goals"]
            for interval in intervals
        )

        total_home_goals = sum(
            interval["home_goals"]
            for interval in intervals
        )

        total_away_goals = sum(
            interval["away_goals"]
            for interval in intervals
        )

        for interval in intervals:
            interval["percentage"] = (
                self._calculate_percentage(
                    value=interval["goals"],
                    total=total_goals,
                )
            )

            interval["home_percentage"] = (
                self._calculate_percentage(
                    value=interval["home_goals"],
                    total=total_home_goals,
                )
            )

            interval["away_percentage"] = (
                self._calculate_percentage(
                    value=interval["away_goals"],
                    total=total_away_goals,
                )
            )

            interval[
                "home_share_in_interval"
            ] = self._calculate_percentage(
                value=interval["home_goals"],
                total=(
                    interval["home_goals"]
                    + interval["away_goals"]
                ),
            )

            interval[
                "away_share_in_interval"
            ] = self._calculate_percentage(
                value=interval["away_goals"],
                total=(
                    interval["home_goals"]
                    + interval["away_goals"]
                ),
            )

        return intervals

    def _load_goal_events(
        self,
        competition_id: int,
    ) -> list[dict]:
        placeholders = ", ".join(
            "?"
            for _ in self.GOAL_EVENT_CODES
        )

        self.cursor.execute(
            f"""
            SELECT
                events.event_id,
                events.minute,
                events.team_id,
                event_types.code,
                matches.home_team_id,
                matches.away_team_id,
                matches.matchday,
                matches.match_date

            FROM events

            INNER JOIN matches
                ON matches.match_id =
                   events.match_id

            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id

            WHERE
                matches.competition_id = ?
                AND event_types.code IN (
                    {placeholders}
                )

            ORDER BY
                matches.matchday ASC,
                matches.match_date ASC,
                events.minute ASC,
                events.event_id ASC
            """,
            (
                competition_id,
                *self.GOAL_EVENT_CODES,
            ),
        )

        events = []

        for row in self.cursor.fetchall():
            events.append(
                {
                    "event_id": int(
                        row[0]
                    ),
                    "minute": row[1],
                    "team_id": (
                        int(row[2])
                        if row[2] is not None
                        else None
                    ),
                    "event_type": row[3],
                    "home_team_id": int(
                        row[4]
                    ),
                    "away_team_id": int(
                        row[5]
                    ),
                    "matchday": row[6],
                    "match_date": row[7],
                }
            )

        return events

    def _create_intervals(
        self,
    ) -> list[dict]:
        intervals = []

        for start, end in self.INTERVALS:
            intervals.append(
                {
                    "label": (
                        f"{start}-{end}"
                    ),
                    "start": start,
                    "end": end,
                    "goals": 0,
                    "percentage": 0.0,
                    "home_goals": 0,
                    "away_goals": 0,
                    "unassigned_goals": 0,
                    "home_percentage": 0.0,
                    "away_percentage": 0.0,
                    "home_share_in_interval": 0.0,
                    "away_share_in_interval": 0.0,
                }
            )

        return intervals

    @staticmethod
    def _get_goal_side(
        event: dict,
    ) -> str | None:
        team_id = event[
            "team_id"
        ]

        if team_id is None:
            return None

        home_team_id = event[
            "home_team_id"
        ]

        away_team_id = event[
            "away_team_id"
        ]

        event_type = str(
            event["event_type"]
        ).upper()

        if event_type == "OWN_GOAL":
            if team_id == home_team_id:
                return "away"

            if team_id == away_team_id:
                return "home"

            return None

        if team_id == home_team_id:
            return "home"

        if team_id == away_team_id:
            return "away"

        return None

    @staticmethod
    def _find_interval(
        minute: int,
        intervals: list[dict],
    ) -> dict | None:
        for interval in intervals:
            if (
                interval["start"]
                <= minute
                <= interval["end"]
            ):
                return interval

        return None

    @staticmethod
    def _normalize_minute(
        minute,
    ) -> int | None:
        if minute is None:
            return None

        if isinstance(
            minute,
            bool,
        ):
            return None

        if isinstance(
            minute,
            int,
        ):
            value = minute

        else:
            text = str(
                minute
            ).strip()

            if not text:
                return None

            if "+" in text:
                text = (
                    text
                    .split(
                        "+",
                        1,
                    )[0]
                    .strip()
                )

            try:
                value = int(
                    text
                )
            except ValueError:
                return None

        if value < 0:
            return None

        return min(
            value,
            90,
        )

    @staticmethod
    def _calculate_percentage(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            (
                value
                / total
            )
            * 100,
            1,
        )