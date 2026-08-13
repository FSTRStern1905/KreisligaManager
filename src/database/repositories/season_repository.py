import sqlite3

from src.database.models.season import Season


class SeasonRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_all(self) -> list[Season]:
        self.cursor.execute(
            """
            SELECT
                season_id,
                name,
                start_date,
                end_date,
                external_id,
                active
            FROM seasons
            ORDER BY start_date DESC
            """
        )

        return [
            self._row_to_season(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_name(
        self,
        name: str,
    ) -> Season | None:
        normalized_name = name.strip()

        if not normalized_name:
            return None

        self.cursor.execute(
            """
            SELECT
                season_id,
                name,
                start_date,
                end_date,
                external_id,
                active
            FROM seasons
            WHERE name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (normalized_name,),
        )

        return self._row_to_season(
            self.cursor.fetchone()
        )

    def get_by_external_id(
        self,
        external_id: str,
    ) -> Season | None:
        normalized_external_id = (
            external_id.strip()
        )

        if not normalized_external_id:
            return None

        self.cursor.execute(
            """
            SELECT
                season_id,
                name,
                start_date,
                end_date,
                external_id,
                active
            FROM seasons
            WHERE external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        )

        return self._row_to_season(
            self.cursor.fetchone()
        )

    def add(
        self,
        season: Season,
    ) -> int:
        normalized_external_id = (
            season.external_id.strip()
            if season.external_id
            else ""
        )

        database_external_id = (
            normalized_external_id
            if normalized_external_id
            else None
        )

        self.cursor.execute(
            """
            INSERT INTO seasons
            (
                name,
                start_date,
                end_date,
                external_id,
                active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                season.name.strip(),
                season.start_date,
                season.end_date,
                database_external_id,
                int(season.active),
            ),
        )

        self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def get_or_create(
        self,
        season: Season,
    ) -> int:
        normalized_external_id = (
            season.external_id.strip()
            if season.external_id
            else ""
        )

        if normalized_external_id:
            existing = self.get_by_external_id(
                normalized_external_id
            )

            if existing is not None:
                return self._require_id(
                    existing
                )

        existing = self.get_by_name(
            season.name
        )

        if existing is not None:
            return self._require_id(
                existing
            )

        return self.add(
            season
        )

    @staticmethod
    def _require_id(
        season: Season,
    ) -> int:
        if season.season_id is None:
            raise ValueError(
                "Die vorhandene Saison besitzt "
                "keine season_id."
            )

        return int(
            season.season_id
        )

    @staticmethod
    def _row_to_season(
        row,
    ) -> Season | None:
        if row is None:
            return None

        return Season(
            season_id=row[0],
            name=row[1],
            start_date=row[2],
            end_date=row[3],
            external_id=row[4] or "",
            active=bool(row[5]),
        )