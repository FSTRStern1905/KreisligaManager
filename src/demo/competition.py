from dataclasses import dataclass


@dataclass(slots=True)
class DemoCompetition:
    season_name: str
    season_start_date: str
    season_end_date: str

    league_name: str
    league_level: int
    league_type: str

    competition_name: str


DEMO_COMPETITION = DemoCompetition(
    season_name="2026/27",
    season_start_date="2026-07-01",
    season_end_date="2027-06-30",
    league_name="Kreisliga A",
    league_level=8,
    league_type="Liga",
    competition_name="Kreisliga A 2026/27",
)