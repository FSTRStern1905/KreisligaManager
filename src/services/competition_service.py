from src.database.models.competition import Competition
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)


class CompetitionService:
    def __init__(self, repository: CompetitionRepository):
        self.repository = repository

    def get_all_competitions(self) -> list[Competition]:
        return self.repository.get_all()

    def get_competition(self, competition_id: int):
        return self.repository.get_by_id(competition_id)

    def create_competition(
        self,
        name: str,
        league_id: int | None,
        season_id: int,
        active: bool = True,
    ) -> int:
        competition = Competition(
            league_id=league_id,
            season_id=season_id,
            name=name.strip(),
            active=active,
        )

        return self.repository.add(competition)

    def delete_competition(self, competition_id: int):
        self.repository.delete(competition_id)

    # ----------------------------------------------------
    # Mannschaften
    # ----------------------------------------------------

    def get_all_teams(self):
        return self.repository.get_all_teams()

    def get_competition_team_ids(
        self,
        competition_id: int,
    ):
        return self.repository.get_competition_team_ids(
            competition_id
        )

    def get_competition_teams(
        self,
        competition_id: int,
    ):
        return self.repository.get_competition_teams(
            competition_id
        )

    def save_competition_teams(
        self,
        competition_id: int,
        team_ids: list[int],
    ):
        self.repository.set_competition_teams(
            competition_id,
            team_ids,
        )