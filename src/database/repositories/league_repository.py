import sqlite3

from src.database.models.league import League


class LeagueRepository:

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_all(self) -> list[League]:
        self.cursor.execute(
            """
            SELECT
                league_id,
                association_id,
                name,
                level,
                season_type
            FROM leagues
            ORDER BY level, name
            """
        )

        return [
            League(
                league_id=row[0],
                association_id=row[1],
                name=row[2],
                level=row[3],
                season_type=row[4],
            )
            for row in self.cursor.fetchall()
        ]

    def get_by_name(
        self,
        association_id: int,
        name: str,
    ) -> League | None:

        self.cursor.execute(
            """
            SELECT
                league_id,
                association_id,
                name,
                level,
                season_type
            FROM leagues
            WHERE
                association_id = ?
                AND name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (
                association_id,
                name.strip(),
            ),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return League(
            league_id=row[0],
            association_id=row[1],
            name=row[2],
            level=row[3],
            season_type=row[4],
        )

    def add(
        self,
        league: League,
    ) -> int:

        self.cursor.execute(
            """
            INSERT INTO leagues
            (
                association_id,
                name,
                level,
                season_type
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                league.association_id,
                league.name,
                league.level,
                league.season_type,
            ),
        )

        self.connection.commit()

        return int(self.cursor.lastrowid)

    def get_or_create(
        self,
        league: League,
    ) -> int:

        existing = self.get_by_name(
            association_id=league.association_id,
            name=league.name,
        )

        if existing is not None:
            return int(existing.league_id)

        return self.add(league)

    def delete(
        self,
        league_id: int,
    ) -> None:

        self.cursor.execute(
            """
            DELETE FROM leagues
            WHERE league_id = ?
            """,
            (league_id,),
        )

        self.connection.commit()