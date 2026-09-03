import sqlite3

from src.database.indexes.indexes import DatabaseIndexes
from src.database.migrations.import_schema_migration import (
    ImportSchemaMigration,
)
from src.database.seed.event_types import EventTypesSeed
from src.database.tables.associations import AssociationsTable
from src.database.tables.clubs import ClubsTable
from src.database.tables.competition_teams import (
    CompetitionTeamsTable,
)
from src.database.tables.competitions import CompetitionsTable
from src.database.tables.countries import CountriesTable
from src.database.tables.event_types import EventTypesTable
from src.database.tables.events import EventsTable
from src.database.tables.formations import FormationsTable
from src.database.tables.leagues import LeaguesTable
from src.database.tables.lineups import LineupsTable
from src.database.tables.match_formations import (
    MatchFormationsTable,
)
from src.database.tables.matches import MatchesTable
from src.database.tables.player_match_stats import (
    PlayerMatchStatsTable,
)
from src.database.tables.players import PlayersTable
from src.database.tables.referees import RefereesTable
from src.database.tables.seasons import SeasonsTable
from src.database.tables.staff import StaffTable
from src.database.tables.standings import StandingsTable
from src.database.tables.stadiums import StadiumsTable
from src.database.tables.team_season_metrics import (
    TeamSeasonMetricsTable,
)
from src.database.tables.teams import TeamsTable
from src.database.tables.weather import WeatherTable


class DatabaseSchema:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create_all_tables(self) -> None:
        self.enable_foreign_keys()

        tables = [
            CountriesTable,
            AssociationsTable,
            SeasonsTable,
            LeaguesTable,
            CompetitionsTable,
            ClubsTable,
            TeamsTable,
            CompetitionTeamsTable,
            TeamSeasonMetricsTable,
            StandingsTable,
            PlayersTable,
            StadiumsTable,
            RefereesTable,
            EventTypesTable,
            MatchesTable,
            LineupsTable,
            PlayerMatchStatsTable,
            EventsTable,
            FormationsTable,
            MatchFormationsTable,
            StaffTable,
            WeatherTable,
        ]

        for table_class in tables:
            table_class(
                self.connection
            ).create()

        self.ensure_competition_sync_columns()

        ImportSchemaMigration(
            self.connection
        ).run()

        DatabaseIndexes(
            self.connection
        ).create()

        EventTypesSeed(
            self.connection
        ).seed()

        self.connection.commit()

    def ensure_competition_sync_columns(
        self,
    ) -> None:
        self.cursor.execute(
            "PRAGMA table_info(competitions);"
        )

        columns = {
            row[1]
            for row in self.cursor.fetchall()
        }

        required_columns = {
            "schedule_url":
                "TEXT NOT NULL DEFAULT ''",
            "last_schedule_sync":
                "TEXT",
        }

        for (
            column_name,
            column_definition,
        ) in required_columns.items():
            if column_name in columns:
                continue

            self.cursor.execute(
                f"""
                ALTER TABLE competitions
                ADD COLUMN {column_name}
                {column_definition};
                """
            )

    def enable_foreign_keys(self) -> None:
        self.cursor.execute(
            "PRAGMA foreign_keys = ON;"
        )