from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
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


COMPETITION_URL = (
    "https://www.fussball.de/spielplan/"
    "regionalliga-suedwest-deutschland-"
    "regionalliga-suedwest-herren-saison2526-"
    "deutschland/-/staffel/"
    "02TN0ODU3400000EVS5489BUVSSD35NB-G"
    "#!/section/matchplan"
)

SOURCE_DB = Path(
    "data/database/kreisligamanager.db"
)

TEST_DB = Path(
    "data/database/"
    "regionalliga_suedwest_2526_import_test.db"
)

BACKUP_DIR = Path(
    "data/database/backups"
)


def prepare_test_database() -> Path:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB nicht gefunden: {SOURCE_DB}"
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    snapshot = (
        BACKUP_DIR
        / (
            "kreisligamanager_before_"
            "regionalliga_test_"
            f"{timestamp}.db"
        )
    )

    shutil.copy2(
        SOURCE_DB,
        snapshot,
    )

    shutil.copy2(
        SOURCE_DB,
        TEST_DB,
    )

    return snapshot


def create_schedule_import_service(
    connection: sqlite3.Connection,
) -> ScheduleImportService:
    return ScheduleImportService(
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


def get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()
    }


def find_regionalliga_competition(
    connection: sqlite3.Connection,
) -> sqlite3.Row | None:
    columns = get_table_columns(
        connection,
        "competitions",
    )

    if not columns:
        return None

    select_parts = [
        "competition_id",
    ]

    for column in (
        "name",
        "external_id",
        "season_id",
        "league_id",
    ):
        if column in columns:
            select_parts.append(
                column
            )

    text_columns = [
        column
        for column in (
            "name",
            "external_id",
        )
        if column in columns
    ]

    if not text_columns:
        return connection.execute(
            f"""
            SELECT
                {", ".join(select_parts)}
            FROM competitions
            ORDER BY competition_id DESC
            LIMIT 1
            """
        ).fetchone()

    where_sql = " OR ".join(
        f'LOWER(COALESCE("{column}", \'\')) '
        f"LIKE '%regionalliga%'"
        for column in text_columns
    )

    return connection.execute(
        f"""
        SELECT
            {", ".join(select_parts)}
        FROM competitions
        WHERE {where_sql}
        ORDER BY competition_id DESC
        LIMIT 1
        """
    ).fetchone()


def print_competition_quality(
    connection: sqlite3.Connection,
    competition_id: int,
) -> None:
    print()
    print("=" * 100)
    print("SCHNELLPRÜFUNG NACH IMPORT")
    print("=" * 100)

    match_row = connection.execute(
        """
        SELECT
            COUNT(*) AS matches_total,
            SUM(
                CASE
                    WHEN status = 'finished'
                    THEN 1
                    ELSE 0
                END
            ) AS matches_finished
        FROM matches
        WHERE competition_id = ?
        """,
        (competition_id,),
    ).fetchone()

    print(
        "Spiele gesamt:      "
        f"{int(match_row['matches_total'] or 0)}"
    )
    print(
        "Spiele beendet:     "
        f"{int(match_row['matches_finished'] or 0)}"
    )

    lineup_row = connection.execute(
        """
        SELECT
            COUNT(*) AS lineup_rows,
            COUNT(
                DISTINCT match_id
            ) AS matches_with_lineups
        FROM lineups
        WHERE match_id IN (
            SELECT match_id
            FROM matches
            WHERE competition_id = ?
        )
        """,
        (competition_id,),
    ).fetchone()

    print(
        "Lineup-Zeilen:      "
        f"{int(lineup_row['lineup_rows'] or 0)}"
    )
    print(
        "Spiele mit Lineup:  "
        f"{int(lineup_row['matches_with_lineups'] or 0)}"
    )

    event_row = connection.execute(
        """
        SELECT
            COUNT(*) AS event_rows,
            COUNT(
                DISTINCT match_id
            ) AS matches_with_events
        FROM events
        WHERE match_id IN (
            SELECT match_id
            FROM matches
            WHERE competition_id = ?
        )
        """,
        (competition_id,),
    ).fetchone()

    print(
        "Event-Zeilen:       "
        f"{int(event_row['event_rows'] or 0)}"
    )
    print(
        "Spiele mit Events:  "
        f"{int(event_row['matches_with_events'] or 0)}"
    )

    stats_table_exists = (
        connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE
                type = 'table'
                AND name = 'player_match_stats'
            """
        ).fetchone()
        is not None
    )

    if stats_table_exists:
        stats_row = connection.execute(
            """
            SELECT
                COUNT(*) AS stat_rows,
                COUNT(
                    DISTINCT match_id
                ) AS matches_with_stats
            FROM player_match_stats
            WHERE match_id IN (
                SELECT match_id
                FROM matches
                WHERE competition_id = ?
            )
            """,
            (competition_id,),
        ).fetchone()

        print(
            "Player-Stats:     "
            f"{int(stats_row['stat_rows'] or 0)}"
        )
        print(
            "Spiele mit Stats: "
            f"{int(stats_row['matches_with_stats'] or 0)}"
        )

    spectator_columns = get_table_columns(
        connection,
        "matches",
    )

    spectator_column = None

    for candidate in (
        "spectators",
        "attendance",
        "spectator_count",
        "attendance_count",
    ):
        if candidate in spectator_columns:
            spectator_column = candidate
            break

    if spectator_column is not None:
        spectator_row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS matches_with_spectators,
                SUM(
                    COALESCE(
                        "{spectator_column}",
                        0
                    )
                ) AS spectators_total
            FROM matches
            WHERE
                competition_id = ?
                AND "{spectator_column}" IS NOT NULL
            """,
            (competition_id,),
        ).fetchone()

        print(
            "Spiele mit Zuschauern: "
            f"{int(spectator_row['matches_with_spectators'] or 0)}"
        )
        print(
            "Zuschauer gesamt:      "
            f"{int(spectator_row['spectators_total'] or 0)}"
        )


def main() -> None:
    print("=" * 100)
    print(
        "REGIONALLIGA SÜDWEST 2025/26 "
        "- VOLLIMPORT-TEST"
    )
    print("=" * 100)

    snapshot = prepare_test_database()

    print(f"Haupt-DB:       {SOURCE_DB}")
    print(f"Test-DB:        {TEST_DB}")
    print(f"Sicherheitskopie: {snapshot}")
    print()
    print(
        "Die Haupt-DB wird NICHT verändert."
    )
    print(
        "Der komplette Import läuft ausschließlich "
        "in der Test-DB."
    )
    print()
    print(
        "URL:"
    )
    print(
        COMPETITION_URL
    )
    print()

    connection = sqlite3.connect(
        TEST_DB
    )
    connection.row_factory = sqlite3.Row

    try:
        schedule_import_service = (
            create_schedule_import_service(
                connection
            )
        )

        importer = CompleteSeasonImporter(
            connection=connection,
            schedule_import_service=(
                schedule_import_service
            ),
        )

        result = importer.import_competition(
            url=COMPETITION_URL,
            headless=True,
            continue_on_detail_error=True,
            max_detail_matches=None,
        )

        connection.commit()

        print()
        print("=" * 100)
        print("IMPORTERGEBNIS")
        print("=" * 100)

        result_dict = result.to_dict()

        for key, value in result_dict.items():
            print(
                f"{key}: {value}"
            )

        competition = (
            find_regionalliga_competition(
                connection
            )
        )

        if competition is None:
            print()
            print(
                "WARNUNG: Importierter Regionalliga-"
                "Wettbewerb konnte für die "
                "Schnellprüfung nicht automatisch "
                "aufgelöst werden."
            )
        else:
            print()
            print(
                "Gefundener Wettbewerb:"
            )
            print(
                dict(competition)
            )

            print_competition_quality(
                connection,
                int(
                    competition[
                        "competition_id"
                    ]
                ),
            )

        print()
        print("=" * 100)
        print(
            "REGIONALLIGA-TESTIMPORT ABGESCHLOSSEN"
        )
        print("=" * 100)
        print(
            f"Test-Datenbank: {TEST_DB}"
        )
        print(
            "Die Hauptdatenbank blieb unverändert."
        )
        print("=" * 100)

    except Exception:
        connection.rollback()

        print()
        print("=" * 100)
        print(
            "REGIONALLIGA-TESTIMPORT ABGEBROCHEN"
        )
        print("=" * 100)
        print(
            "Die Hauptdatenbank wurde nicht verändert."
        )
        print(
            f"Test-Datenbank bleibt zur Diagnose erhalten: "
            f"{TEST_DB}"
        )
        print("=" * 100)

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
