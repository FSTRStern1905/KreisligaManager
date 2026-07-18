import sqlite3


class GoalTimelineService:
    INTERVALS = [
        (0, 15),
        (16, 30),
        (31, 45),
        (46, 60),
        (61, 75),
        (76, 90),
    ]

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
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

        self.cursor.execute(
        """
        SELECT
            events.minute
        FROM events
        INNER JOIN matches
            ON matches.match_id = events.match_id
        INNER JOIN event_types
            ON event_types.event_type_id = events.event_type_id
        WHERE
            matches.competition_id = ?
            AND event_types.code IN (
                'GOAL',
                'OWN_GOAL',
                'PENALTY_GOAL'
            )
        """,
        (competition_id,),
            )
        

        for (minute,) in self.cursor.fetchall():
            normalized_minute = (
                self._normalize_minute(
                    minute
                )
            )

            interval = self._find_interval(
                minute=normalized_minute,
                intervals=intervals,
            )

            if interval is not None:
                interval["goals"] += 1

        total_goals = sum(
            interval["goals"]
            for interval in intervals
        )

        for interval in intervals:
            if total_goals == 0:
                interval["percentage"] = 0.0
            else:
                interval["percentage"] = round(
                    (
                        interval["goals"]
                        / total_goals
                    )
                    * 100,
                    1,
                )

        return intervals

    def _create_intervals(
        self,
    ) -> list[dict]:
        result = []

        for start, end in self.INTERVALS:
            result.append(
                {
                    "label": f"{start}-{end}",
                    "start": start,
                    "end": end,
                    "goals": 0,
                    "percentage": 0.0,
                }
            )

        return result

    def _find_interval(
        self,
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

    def _normalize_minute(
        self,
        minute,
    ) -> int:
        if minute is None:
            return 0

        if isinstance(minute, int):
            return min(
                max(minute, 0),
                90,
            )

        text = str(minute).strip()

        if "+" in text:
            text = text.split("+")[0]

        try:
            value = int(text)
        except ValueError:
            value = 0

        return min(
            max(value, 0),
            90,
        )