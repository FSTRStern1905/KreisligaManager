from __future__ import annotations

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class MinutesCalculator:
    DEFAULT_MATCH_LENGTH = 90

    def apply(
        self,
        stats: list[PlayerMatchStat],
    ) -> None:
        for stat in stats:
            self._calculate(
                stat
            )

    def _calculate(
        self,
        stat: PlayerMatchStat,
    ) -> None:
        if (
            stat.minute_in is None
            and not stat.was_substituted_in
        ):
            stat.minute_out = None
            stat.minutes_played = 0
            return

        minute_in = (
            stat.minute_in
            if stat.minute_in is not None
            else 0
        )

        minute_out = (
            stat.minute_out
            if stat.minute_out is not None
            else self.DEFAULT_MATCH_LENGTH
        )

        minute_in = max(
            0,
            int(minute_in),
        )

        minute_out = min(
            self.DEFAULT_MATCH_LENGTH,
            int(minute_out),
        )

        if minute_out < minute_in:
            minute_out = minute_in

        stat.minute_in = minute_in
        stat.minute_out = minute_out
        stat.minutes_played = (
            minute_out - minute_in
        )