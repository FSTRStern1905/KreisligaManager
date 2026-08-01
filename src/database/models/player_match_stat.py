from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PlayerMatchStat:
    player_match_stat_id: int | None

    match_id: int
    team_id: int
    player_id: int

    is_starting: bool

    was_substituted_in: bool
    was_substituted_out: bool

    minute_in: int | None
    minute_out: int | None
    minutes_played: int

    goals: int
    own_goals: int
    assists: int

    yellow_cards: int
    yellow_red_cards: int
    red_cards: int

    clean_sheet: bool

    shirt_number: int | None
    position: str

    created_at: str | None = None
    updated_at: str | None = None