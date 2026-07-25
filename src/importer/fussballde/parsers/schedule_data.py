from dataclasses import dataclass, field


@dataclass(slots=True)
class ScheduleMatch:
    match_id: str
    fixture_number: int | None
    matchday: int | None
    date: str
    time: str
    competition: str
    category: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: str
    match_url: str


@dataclass(slots=True)
class ScheduleData:
    league_name: str = ""
    league_external_id: str = ""
    association_name: str = ""
    season_name: str = ""
    competition_name: str = ""
    category: str = ""

    matches: list[ScheduleMatch] = field(
        default_factory=list
    )