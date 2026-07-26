from dataclasses import dataclass, field


@dataclass(slots=True)
class MatchEvent:
    minute: int | None = None
    additional_time: int = 0

    event_type: str = ""

    team: str = ""
    player: str = ""
    player_out: str = ""

    value: str = ""
    description: str = ""


@dataclass(slots=True)
class MatchDetailData:
    match_id: str = ""

    home_team: str = ""
    away_team: str = ""

    home_goals: int | None = None
    away_goals: int | None = None

    halftime_home: int | None = None
    halftime_away: int | None = None

    stadium: str = ""
    referee: str = ""
    attendance: int | None = None

    events: list[MatchEvent] = field(
        default_factory=list
    )