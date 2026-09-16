import sqlite3


class ImportSchemaMigration:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def run(self) -> None:
        self._extend_clubs_table()
        self._extend_leagues_table()
        self._extend_seasons_table()
        self._extend_competitions_table()
        self._extend_teams_table()
        self._extend_players_table()
        self._extend_matches_table()
        self._extend_events_table()

        self._create_import_indexes()

        self.connection.commit()

    def _extend_clubs_table(self) -> None:
        self._add_column_if_missing(
            table="clubs",
            column="external_id",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="clubs",
            column="founded",
            definition="INTEGER",
        )
        self._add_column_if_missing(
            table="clubs",
            column="country",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="clubs",
            column="website",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="clubs",
            column="logo",
            definition="TEXT",
        )

    def _extend_leagues_table(self) -> None:
        self._add_column_if_missing(
            table="leagues",
            column="external_id",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="leagues",
            column="country",
            definition="TEXT",
        )

    def _extend_seasons_table(self) -> None:
        self._add_column_if_missing(
            table="seasons",
            column="external_id",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="seasons",
            column="active",
            definition="INTEGER NOT NULL DEFAULT 0",
        )

    def _extend_competitions_table(self) -> None:
        self._add_column_if_missing(
            table="competitions",
            column="source",
            definition="TEXT NOT NULL DEFAULT 'manual'",
        )

    def _extend_teams_table(self) -> None:
        self._add_column_if_missing(
            table="teams",
            column="external_id",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="teams",
            column="coach",
            definition="TEXT",
        )
        self._add_column_if_missing(
            table="teams",
            column="age_group",
            definition="TEXT",
        )

    def _extend_players_table(self) -> None:
        self._add_column_if_missing(
            table="players",
            column="external_id",
            definition="TEXT",
        )

    def _extend_matches_table(self) -> None:
        self._add_column_if_missing(
            table="matches",
            column="external_id",
            definition="TEXT",
        )

    def _extend_events_table(self) -> None:
        self._add_column_if_missing(
            table="events",
            column="external_id",
            definition="TEXT",
        )

    def _create_import_indexes(self) -> None:
        indexes = [
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_clubs_external_id
            ON clubs(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_leagues_external_id
            ON leagues(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_seasons_external_id
            ON seasons(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_teams_external_id
            ON teams(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_players_external_id
            ON players(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_matches_external_id
            ON matches(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_events_external_id
            ON events(external_id)
            WHERE external_id IS NOT NULL;
            """,
        ]

        for index in indexes:
            self.cursor.execute(index)

    def _add_column_if_missing(
        self,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        columns = self._get_columns(
            table
        )

        if column in columns:
            return

        self.cursor.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {definition};
            """
        )

    def _get_columns(
        self,
        table: str,
    ) -> set[str]:
        self.cursor.execute(
            f"PRAGMA table_info({table});"
        )

        return {
            row[1]
            for row in self.cursor.fetchall()
        }