from dataclasses import dataclass


@dataclass
class Standing:
    standing_id: int | None = None
    competition_id: int | None = None
    season_id: int | None = None
    team_id: int | None = None

    position: int = 0
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0

    team_name: str = ""