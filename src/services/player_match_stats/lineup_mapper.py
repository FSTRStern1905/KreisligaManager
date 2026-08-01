from __future__ import annotations

from src.database.models.player_match_stat import (
    PlayerMatchStat,
)


class LineupMapper:
    def build(
        self,
        lineups: list[dict],
    ) -> list[PlayerMatchStat]:
        stats: list[PlayerMatchStat] = []

        for lineup in lineups:
            is_starting = bool(
                lineup["is_starting"]
            )

            stats.append(
                PlayerMatchStat(
                    player_match_stat_id=None,
                    match_id=int(
                        lineup["match_id"]
                    ),
                    team_id=int(
                        lineup["team_id"]
                    ),
                    player_id=int(
                        lineup["player_id"]
                    ),
                    is_starting=is_starting,
                    was_substituted_in=False,
                    was_substituted_out=False,
                    minute_in=(
                        0
                        if is_starting
                        else None
                    ),
                    minute_out=(
                        90
                        if is_starting
                        else None
                    ),
                    minutes_played=(
                        90
                        if is_starting
                        else 0
                    ),
                    goals=0,
                    own_goals=0,
                    assists=0,
                    yellow_cards=0,
                    yellow_red_cards=0,
                    red_cards=0,
                    clean_sheet=False,
                    shirt_number=lineup.get(
                        "shirt_number"
                    ),
                    position=str(
                        lineup.get(
                            "position",
                            "",
                        )
                    ),
                )
            )

        return stats