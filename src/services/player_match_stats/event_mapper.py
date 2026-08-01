from __future__ import annotations

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class EventMapper:
    def apply(
        self,
        stats: list[PlayerMatchStat],
        events: list[dict],
    ) -> None:
        players = {
            stat.player_id: stat
            for stat in stats
        }

        for event in events:
            player_id = event.get(
                "player_id"
            )

            if player_id is None:
                continue

            stat = players.get(
                player_id
            )

            if stat is None:
                continue

            event_type = str(
                event.get(
                    "event_type_code",
                    "",
                )
            ).strip().upper()

            minute = event.get(
                "minute"
            )

            match event_type:
                case "GOAL" | "PENALTY_GOAL":
                    stat.goals += 1

                case "OWN_GOAL":
                    stat.own_goals += 1

                case "YELLOW_CARD":
                    stat.yellow_cards += 1

                case "YELLOW_RED_CARD":
                    stat.yellow_red_cards += 1

                    if minute is not None:
                        stat.minute_out = int(
                            minute
                        )

                case "RED_CARD":
                    stat.red_cards += 1

                    if minute is not None:
                        stat.minute_out = int(
                            minute
                        )

                case "SUBSTITUTION_IN":
                    stat.was_substituted_in = True

                    if minute is not None:
                        stat.minute_in = int(
                            minute
                        )

                case "SUBSTITUTION_OUT":
                    stat.was_substituted_out = True

                    if minute is not None:
                        stat.minute_out = int(
                            minute
                        )