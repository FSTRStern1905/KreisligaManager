from __future__ import annotations

from pathlib import Path

from src.database.database import Database
from src.database.schema import DatabaseSchema
from src.database.repositories.association_repository import (
    AssociationRepository,
)
from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import (
    LeagueRepository,
)
from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.database.repositories.season_repository import (
    SeasonRepository,
)
from src.database.repositories.team_repository import (
    TeamRepository,
)
from src.importer.fussballde.complete_season_importer import (
    CompleteSeasonImporter,
)
from src.services.imports.schedule_import_service import (
    ScheduleImportService,
)


COMPETITION_URL = (
    "https://www.fussball.de/spielplan/kreisliga-a7-kreis-trier-saarburg-kreisliga-a-herren-saison2526-rheinland/-/staffel/02TN13LMJO000008VS5489BUVSSD35NB-G#!/section/matchplan"
)


def main() -> None:

    test_db = Path(
        "data/database/kreisligamanager_test.db"
    )

    if test_db.exists():
        test_db.unlink()

    database = Database(
        database_name="kreisligamanager_test.db",
    )

    connection = database.connect()

    schema = DatabaseSchema(connection)
    schema.create_all_tables()

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
            max_detail_matches= 5,
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