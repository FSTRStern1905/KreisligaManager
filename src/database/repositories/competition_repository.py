import sqlite3

from src.database.models.competition import Competition


class CompetitionRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_all(self) -> list[Competition]:
        self.cursor.execute(
            """
            SELECT
                competition_id,
                league_id,
                season_id,
                name,
                active
            FROM competitions
            ORDER BY name
            """
        )

        competitions = []

        for row in self.cursor.fetchall():
            competitions.append(
                Competition(
                    competition_id=row[0],
                    league_id=row[1],
                    season_id=row[2],
                    name=row[3],
                    active=bool(row[4]),
                )
            )

        return competitions

    def get_by_id(self, competition_id: int) -> Competition | None:
        self.cursor.execute(
            """
            SELECT
                competition_id,
                league_id,
                season_id,
                name,
                active
            FROM competitions
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return Competition(
            competition_id=row[0],
            league_id=row[1],
            season_id=row[2],
            name=row[3],
            active=bool(row[4]),
        )

    def add(self, competition: Competition) -> int:
        self.cursor.execute(
            """
            INSERT INTO competitions (
                league_id,
                season_id,
                name,
                active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                competition.league_id,
                competition.season_id,
                competition.name,
                int(competition.active),
            ),
        )

        self.connection.commit()

        return self.cursor.lastrowid

    def delete(self, competition_id: int):
        self.cursor.execute(
            """
            DELETE FROM competitions
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        self.connection.commit()

    def get_all_teams(self) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                clubs.name,
                teams.name,
                teams.short_name,
                teams.team_number
            FROM teams
            INNER JOIN clubs
                ON clubs.club_id = teams.club_id
            ORDER BY
                clubs.name,
                teams.team_number,
                teams.name
            """
        )

        return self.cursor.fetchall()

    def get_competition_team_ids(
        self,
        competition_id: int,
    ) -> list[int]:
        self.cursor.execute(
            """
            SELECT team_id
            FROM competition_teams
            WHERE competition_id = ?
            ORDER BY team_id
            """,
            (competition_id,),
        )

        return [row[0] for row in self.cursor.fetchall()]

    def get_competition_teams(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                clubs.name,
                teams.name,
                teams.short_name,
                teams.team_number
            FROM competition_teams
            INNER JOIN teams
                ON teams.team_id = competition_teams.team_id
            INNER JOIN clubs
                ON clubs.club_id = teams.club_id
            WHERE competition_teams.competition_id = ?
            ORDER BY
                clubs.name,
                teams.team_number,
                teams.name
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def set_competition_teams(
        self,
        competition_id: int,
        team_ids: list[int],
    ):
        self.cursor.execute(
            """
            DELETE FROM competition_teams
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        for team_id in team_ids:
            self.cursor.execute(
                """
                INSERT INTO competition_teams (
                    competition_id,
                    team_id
                )
                VALUES (?, ?)
                """,
                (
                    competition_id,
                    team_id,
                ),
            )

        self.connection.commit()