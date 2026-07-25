import sqlite3

from src.database.models.season import Season


class SeasonRepository:
    def __init__(self, connection: sqlite3.Connection):
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

        seasons = []

        for row in self.cursor.fetchall():
            seasons.append(
                Season(
                    season_id=row[0],
                    name=row[1],
                    start_date=row[2],
                    end_date=row[3],
                    external_id=row[4] or "",
                    active=bool(row[5]),
                )
            )

        return seasons

    def get_by_name(
        self,
        name: str,
    ) -> Season | None:
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
            WHERE name = ?
            """,
            (name,),
        )

        row = self.cursor.fetchone()

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

    def add(
        self,
        season: Season,
    ) -> int:
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
                season.name,
                season.start_date,
                season.end_date,
                season.external_id,
                int(season.active),
            ),
        )

        self.connection.commit()

        return self.cursor.lastrowid

    def get_or_create(
        self,
        season: Season,
    ) -> int:
        existing = self.get_by_name(
            season.name
        )

        if existing is not None:
            return existing.season_id

        return self.add(season)