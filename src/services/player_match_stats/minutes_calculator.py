from __future__ import annotations

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class MinutesCalculator:
    """
    Finalisiert die bereits vom EventMapper berechneten
    Einsatzzeiten.

    WICHTIG:
    Einsatzminuten dürfen NICHT erneut ausschließlich aus
    minute_in/minute_out berechnet werden.

    Im Amateurfußball sind Rück-/Mehrfachwechsel möglich.
    Ein Spieler kann dadurch mehrere Einsatzintervalle haben,
    z. B.:

        0-56 + 80-90 = 66 Minuten

    minute_in und minute_out bilden dabei nur den ersten
    Einstieg bzw. ersten Ausstieg ab. Die vollständige
    Einsatzzeit wird vom EventMapper über alle Intervalle
    berechnet und hier lediglich validiert/normalisiert.
    """

    MIN_MINUTE = 0
    MAX_MINUTE = 90

    def apply(
        self,
        stats: list[PlayerMatchStat],
    ) -> None:
        for stat in stats:
            self._normalize_stat(
                stat
            )

    def _normalize_stat(
        self,
        stat: PlayerMatchStat,
    ) -> None:
        stat.is_starting = bool(
            stat.is_starting
        )

        stat.was_substituted_in = bool(
            stat.was_substituted_in
        )

        stat.was_substituted_out = bool(
            stat.was_substituted_out
        )

        if stat.is_starting:
            stat.minute_in = 0

        stat.minute_in = (
            self._normalize_optional_minute(
                stat.minute_in
            )
        )

        stat.minute_out = (
            self._normalize_optional_minute(
                stat.minute_out
            )
        )

        try:
            minutes_played = int(
                stat.minutes_played
            )
        except (
            TypeError,
            ValueError,
        ):
            minutes_played = 0

        stat.minutes_played = max(
            self.MIN_MINUTE,
            min(
                minutes_played,
                self.MAX_MINUTE,
            ),
        )

        if (
            not stat.is_starting
            and not stat.was_substituted_in
        ):
            stat.minute_in = None

            if (
                not stat.was_substituted_out
            ):
                stat.minute_out = None

            stat.minutes_played = 0

    @classmethod
    def _normalize_optional_minute(
        cls,
        value: int | None,
    ) -> int | None:
        if value is None:
            return None

        try:
            minute = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return max(
            cls.MIN_MINUTE,
            min(
                minute,
                cls.MAX_MINUTE,
            ),
        )
