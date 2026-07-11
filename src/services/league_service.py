from src.database.models.league import League
from src.database.repositories.league_repository import LeagueRepository


class LeagueService:
    def __init__(self, repository: LeagueRepository):
        self.repository = repository

    def get_all_leagues(self) -> list[League]:
        return self.repository.get_all()

    def create_league(
        self,
        name: str,
        level: int,
        association_id: int | None = None,
        season_type: str = "Liga",
    ):
        league = League(
            association_id=association_id,
            name=name.strip(),
            level=level,
            season_type=season_type,
        )

        self.repository.add(league)

    def delete_league(self, league_id: int):
        self.repository.delete(league_id)