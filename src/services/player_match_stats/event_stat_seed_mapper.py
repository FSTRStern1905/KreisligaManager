from __future__ import annotations

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class EventStatSeedMapper:
    SUBSTITUTION_CODES = {
        "SUBSTITUTION_IN",
        "SUBSTITUTION_OUT",
    }

    def extend(
        self,
        stats: list[PlayerMatchStat],
        events: list[dict],
    ) -> int:
        existing_player_ids = {
            stat.player_id
            for stat in stats
        }

        created = 0

        for event in events:
            event_type = str(
                event.get(
                    "event_type_code",
                    "",
                )
            ).strip().upper()

            if event_type not in self.SUBSTITUTION_CODES:
                continue

            player_id = event.get(
                "player_id"
            )
            team_id = event.get(
                "team_id"
            )

            if (
                player_id is None
                or team_id is None
            ):
                continue

            player_id = int(
                player_id
            )
            team_id = int(
                team_id
            )

            if player_id in existing_player_ids:
                continue

            stats.append(
                PlayerMatchStat(
                    player_match_stat_id=None,
                    match_id=int(
                        event["match_id"]
                    ),
                    team_id=team_id,
                    player_id=player_id,

                    # Fehlt der Spieler im Lineup, kennen
                    # wir seine ursprüngliche Rolle nicht
                    # sicher. Deshalb niemals Startelf
                    # künstlich ableiten.
                    is_starting=False,

                    was_substituted_in=False,
                    was_substituted_out=False,

                    minute_in=None,
                    minute_out=None,
                    minutes_played=0,

                    goals=0,
                    own_goals=0,
                    assists=0,

                    yellow_cards=0,
                    yellow_red_cards=0,
                    red_cards=0,

                    clean_sheet=False,

                    shirt_number=None,
                    position="",
                )
            )

            existing_player_ids.add(
                player_id
            )
            created += 1

        return created
