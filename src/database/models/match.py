from dataclasses import dataclass


@dataclass(slots=True)
class Match:
    match_id: int | None = None

    competition_id: int | None = None
    season_id: int | None = None
    league_id: int | None = None

    matchday: int | None = None
    match_date: str | None = None
    kickoff_time: str | None = None

    home_team_id: int | None = None
    away_team_id: int | None = None

    stadium_id: int | None = None
    referee_id: int | None = None

    attendance: int | None = None

    home_goals: int | None = None
    away_goals: int | None = None

    status: str = "scheduled"
    notes: str = ""

    home_team_name: str = ""
    away_team_name: str = ""

    @property
    def result_text(self) -> str:
        if self.home_goals is None or self.away_goals is None:
            return "- : -"

        return f"{self.home_goals} : {self.away_goals}"

    @property
    def display_name(self) -> str:
        return (
            f"{self.home_team_name} "
            f"{self.result_text} "
            f"{self.away_team_name}"
        )

    @property
    def is_finished(self) -> bool:
        return self.status == "finished"

    @property
    def is_scheduled(self) -> bool:
        return self.status == "scheduled"