from __future__ import annotations

import sqlite3
import traceback
from pathlib import Path

from src.database.repositories.association_repository import (
    AssociationRepository,
)
from src.database.repositories.club_repository import (
    ClubRepository,
)
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


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

STAFFEL_URL = (
    "https://www.fussball.de/spielplan/"
    "reserveklasse-trier-saarburg-kreis-trier-saarburg-"
    "reserveklasse-herren-saison2627-rheinland/-/staffel/"
    "031C6B2G10000009VS5489BTVUS470OH-G"
    "#!/section/matchplan"
)


def main() -> None:
    print("=" * 78)
    print("RESERVEKLASSE TRIER-SAARBURG - KONSOLENIMPORT")
    print("=" * 78)
    print(f"Datenbank: {DATABASE_PATH}")
    print(f"URL: {STAFFEL_URL}")
    print()

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        schedule_import_service = (
            ScheduleImportService(
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
        )

        importer = CompleteSeasonImporter(
            connection=connection,
            schedule_import_service=(
                schedule_import_service
            ),
        )

        print("Import wird gestartet ...")
        print()

        result = importer.import_competition(
            url=STAFFEL_URL,
            headless=False,
            continue_on_detail_error=True,
            max_detail_matches=None,
        )

        connection.commit()

        print()
        print("=" * 78)
        print("IMPORT ABGESCHLOSSEN")
        print("=" * 78)

        result_data = result.to_dict()

        for key, value in result_data.items():
            print(
                f"{key}: {value}"
            )

        print()
        print(
            "competition_id:",
            schedule_import_service.last_competition_id,
        )

        if result.errors:
            print()
            print("-" * 78)
            print("DETAILFEHLER")
            print("-" * 78)

            for index, error in enumerate(
                result.errors,
                start=1,
            ):
                print(
                    f"{index:03d}: {error}"
                )

    except Exception as error:
        connection.rollback()

        print()
        print("=" * 78)
        print("IMPORT ABGEBROCHEN")
        print("=" * 78)
        print(
            f"{type(error).__name__}: {error}"
        )
        print()
        traceback.print_exc()

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
