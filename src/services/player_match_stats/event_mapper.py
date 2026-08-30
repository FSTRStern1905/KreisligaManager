from __future__ import annotations

from collections import defaultdict

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class EventMapper:
    REGULATION_MINUTES = 90

    SUBSTITUTION_IN = "SUBSTITUTION_IN"
    SUBSTITUTION_OUT = "SUBSTITUTION_OUT"

    RED_CARD_CODES = {
        "RED_CARD",
        "YELLOW_RED_CARD",
    }

    def apply(
        self,
        stats: list[PlayerMatchStat],
        events: list[dict],
    ) -> None:
        players = {
            int(stat.player_id): stat
            for stat in stats
        }

        player_events: dict[
            int,
            list[tuple[int, dict]],
        ] = defaultdict(list)

        for index, event in enumerate(events):
            player_id = event.get("player_id")

            if player_id is None:
                continue

            player_id = int(player_id)

            stat = players.get(player_id)

            if stat is None:
                continue

            event_type = self._event_type(event)

            match event_type:
                case "GOAL" | "PENALTY_GOAL":
                    stat.goals += 1

                case "OWN_GOAL":
                    stat.own_goals += 1

                case "YELLOW_CARD":
                    stat.yellow_cards += 1

                case "YELLOW_RED_CARD":
                    stat.yellow_red_cards += 1

                case "RED_CARD":
                    stat.red_cards += 1

            if event_type in {
                self.SUBSTITUTION_IN,
                self.SUBSTITUTION_OUT,
                *self.RED_CARD_CODES,
            }:
                player_events[player_id].append(
                    (index, event)
                )

        for player_id, stat in players.items():
            self._apply_playing_time(
                stat=stat,
                events=player_events.get(
                    player_id,
                    [],
                ),
            )

    def _apply_playing_time(
        self,
        stat: PlayerMatchStat,
        events: list[tuple[int, dict]],
    ) -> None:
        ordered_events = sorted(
            events,
            key=self._event_sort_key,
        )

        is_starting = bool(
            stat.is_starting
        )

        active = is_starting

        interval_start: int | None = (
            0
            if is_starting
            else None
        )

        minutes_played = 0

        first_in: int | None = None
        first_out: int | None = None

        was_substituted_in = False
        was_substituted_out = False

        sent_off = False
        has_unknown_substitution_time = False

        for _, event in ordered_events:
            event_type = self._event_type(event)
            raw_minute = event.get("minute")

            if (
                event_type in {
                    self.SUBSTITUTION_IN,
                    self.SUBSTITUTION_OUT,
                }
                and self._is_unknown_substitution_minute(
                    raw_minute
                )
            ):
                has_unknown_substitution_time = True

                if event_type == self.SUBSTITUTION_IN:
                    was_substituted_in = True

                if event_type == self.SUBSTITUTION_OUT:
                    was_substituted_out = True

                continue

            if raw_minute is None:
                continue

            minute = self._normalize_minute(
                raw_minute
            )

            if event_type == self.SUBSTITUTION_OUT:
                was_substituted_out = True

                if first_out is None:
                    first_out = minute

                if (
                    active
                    and interval_start is not None
                ):
                    minutes_played += max(
                        0,
                        minute - interval_start,
                    )

                    active = False
                    interval_start = None

                continue

            if event_type == self.SUBSTITUTION_IN:
                was_substituted_in = True

                if first_in is None:
                    first_in = minute

                if sent_off:
                    continue

                if not active:
                    active = True
                    interval_start = minute

                continue

            if event_type in self.RED_CARD_CODES:
                if first_out is None:
                    first_out = minute

                if (
                    active
                    and interval_start is not None
                ):
                    minutes_played += max(
                        0,
                        minute - interval_start,
                    )

                active = False
                interval_start = None
                sent_off = True

        if has_unknown_substitution_time:
            stat.was_substituted_in = (
                was_substituted_in
            )
            stat.was_substituted_out = (
                was_substituted_out
            )

            stat.minute_in = (
                0
                if is_starting
                else None
            )
            stat.minute_out = None

            stat.minutes_played = 0
            return

        if (
            active
            and interval_start is not None
        ):
            minutes_played += max(
                0,
                self.REGULATION_MINUTES
                - interval_start,
            )

        stat.was_substituted_in = (
            was_substituted_in
        )
        stat.was_substituted_out = (
            was_substituted_out
        )

        if is_starting:
            stat.minute_in = 0
        else:
            stat.minute_in = first_in

        if first_out is not None:
            stat.minute_out = first_out
        elif (
            is_starting
            or first_in is not None
        ):
            stat.minute_out = (
                self.REGULATION_MINUTES
            )
        else:
            stat.minute_out = None

        stat.minutes_played = int(
            minutes_played
        )

    @classmethod
    def _event_sort_key(
        cls,
        item: tuple[int, dict],
    ) -> tuple[int, int]:
        original_index, event = item

        raw_minute = event.get("minute")

        if cls._is_unknown_substitution_minute(
            raw_minute
        ):
            minute = -1
        else:
            minute = cls._normalize_minute(
                raw_minute
            )

        return (
            minute,
            original_index,
        )

    @staticmethod
    def _event_type(
        event: dict,
    ) -> str:
        return str(
            event.get(
                "event_type_code",
                "",
            )
        ).strip().upper()

    @classmethod
    def _is_unknown_substitution_minute(
        cls,
        value: object,
    ) -> bool:
        if value is None:
            return True

        try:
            minute = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return True

        return minute <= 0

    @classmethod
    def _normalize_minute(
        cls,
        value: object,
    ) -> int:
        try:
            minute = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(
            0,
            min(
                minute,
                cls.REGULATION_MINUTES,
            ),
        )
