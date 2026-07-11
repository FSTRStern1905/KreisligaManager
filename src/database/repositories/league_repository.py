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

        leagues = []

        for row in self.cursor.fetchall():
            leagues.append(
                League(
                    league_id=row[0],
                    association_id=row[1],
                    name=row[2],
                    level=row[3],
                    season_type=row[4],
                )
            )

        return leagues

    def add(self, league: League):
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

    def delete(self, league_id: int):
        self.cursor.execute(
            """
            DELETE FROM leagues
            WHERE league_id = ?
            """,
            (league_id,),
        )

        self.connection.commit()