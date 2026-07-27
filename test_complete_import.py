from __future__ import annotations

from src.database.database import Database
from src.database.repositories.association_repository import (
    AssociationRepository,
)
from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import LeagueRepository
from src.database.repositories.match_repository import MatchRepository
from src.database.repositories.season_repository import SeasonRepository
from src.database.repositories.team_repository import TeamRepository
from src.importer.fussballde.complete_season_importer import (
    CompleteSeasonImporter,
)
from src.services.imports.schedule_import_service import (
    ScheduleImportService,
)


COMPETITION_URL = (
    "https://www.fussball.de/spieltagsuebersicht/kreisliga-a7-kreis-trier-saarburg-kreisliga-a-herren-saison2526-rheinland/-/staffel/02TN13LMJO000008VS5489BUVSSD35NB-G#!/"
)


def main() -> None:
    database = Database()
    connection = database.connect()

    try:
        schedule_import_service = ScheduleImportService(
            association_repository=AssociationRepository(
                connection
            ),
            league_repository=LeagueRepository(
                connection
            ),
            season_repository=SeasonRepository(
                connection
            ),
            club_repository=ClubRepository(
                connection
            ),
            team_repository=TeamRepository(
                connection
            ),
            competition_repository=CompetitionRepository(
                connection
            ),
            match_repository=MatchRepository(
                connection
            ),
        )

        importer = CompleteSeasonImporter(
            connection=connection,
            schedule_import_service=(
                schedule_import_service
            ),
        )

        result = importer.import_competition(
            url=COMPETITION_URL,
            headless=False,
            continue_on_detail_error=True,
        )

        print()
        print("=" * 60)
        print("KOMPLETTIMPORT ABGESCHLOSSEN")
        print("=" * 60)

        for key, value in result.to_dict().items():
            print(f"{key}: {value}")

    finally:
        database.close()


if __name__ == "__main__":
    main()