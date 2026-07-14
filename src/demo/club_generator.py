import sqlite3

from src.demo.clubs import DEMO_CLUBS


class DemoClubGenerator:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def generate(self) -> dict[str, int]:
        team_ids: dict[str, int] = {}

        for club in DEMO_CLUBS:
            club_id = self._get_or_create_club(
                name=club.name,
                short_name=club.short_name,
                city=club.city,
            )

            team_id = self._get_or_create_team(
                club_id=club_id,
                name=club.name,
                short_name=club.short_name,
                team_number=1,
            )

            team_ids[club.name] = team_id

        return team_ids

    def _get_or_create_club(
        self,
        name: str,
        short_name: str,
        city: str,
    ) -> int:
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO clubs (
                name,
                short_name,
                city
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                short_name,
                city,
            ),
        )

        self.cursor.execute(
            """
            SELECT club_id
            FROM clubs
            WHERE name = ?
            """,
            (name,),
        )

        result = self.cursor.fetchone()

        if result is None:
            raise ValueError(
                f"Verein konnte nicht gefunden werden: {name}"
            )

        return result[0]

    def _get_or_create_team(
        self,
        club_id: int,
        name: str,
        short_name: str,
        team_number: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT team_id
            FROM teams
            WHERE
                club_id = ?
                AND team_number = ?
            ORDER BY team_id
            LIMIT 1
            """,
            (
                club_id,
                team_number,
            ),
        )

        result = self.cursor.fetchone()

        if result is not None:
            return result[0]

        self.cursor.execute(
            """
            INSERT INTO teams (
                club_id,
                name,
                short_name,
                team_number
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                club_id,
                name,
                short_name,
                team_number,
            ),
        )

        return self.cursor.lastrowid