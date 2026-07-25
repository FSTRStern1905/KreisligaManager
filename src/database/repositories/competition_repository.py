import sqlite3

from src.database.models.competition import Competition


class CompetitionRepository:

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
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
            ORDER BY name ASC
            """
        )

        return [
            self._create_competition(row)
            for row in self.cursor.fetchall()
        ]

    def get(
        self,
        competition_id: int,
    ) -> Competition | None:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

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
            LIMIT 1
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return self._create_competition(row)

    def get_by_id(
        self,
        competition_id: int,
    ) -> Competition | None:
        return self.get(
            competition_id
        )

    def get_by_name(
        self,
        league_id: int,
        season_id: int,
        name: str,
    ) -> Competition | None:
        normalized_name = name.strip()

        if league_id <= 0:
            raise ValueError(
                "Ungültige Liga-ID."
            )

        if season_id <= 0:
            raise ValueError(
                "Ungültige Saison-ID."
            )

        if not normalized_name:
            return None

        self.cursor.execute(
            """
            SELECT
                competition_id,
                league_id,
                season_id,
                name,
                active
            FROM competitions
            WHERE
                league_id = ?
                AND season_id = ?
                AND name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (
                league_id,
                season_id,
                normalized_name,
            ),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return self._create_competition(row)

    def add(
        self,
        competition: Competition,
    ) -> int:
        normalized_name = competition.name.strip()

        if competition.league_id <= 0:
            raise ValueError(
                "Ungültige Liga-ID."
            )

        if competition.season_id <= 0:
            raise ValueError(
                "Ungültige Saison-ID."
            )

        if not normalized_name:
            raise ValueError(
                "Der Wettbewerbsname darf nicht leer sein."
            )

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
                normalized_name,
                int(competition.active),
            ),
        )

        self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def get_or_create(
        self,
        league_id: int,
        season_id: int,
        name: str,
        active: bool = True,
    ) -> int:
        normalized_name = name.strip()

        if league_id <= 0:
            raise ValueError(
                "Ungültige Liga-ID."
            )

        if season_id <= 0:
            raise ValueError(
                "Ungültige Saison-ID."
            )

        if not normalized_name:
            raise ValueError(
                "Der Wettbewerbsname darf nicht leer sein."
            )

        existing_competition = self.get_by_name(
            league_id=league_id,
            season_id=season_id,
            name=normalized_name,
        )

        if existing_competition is not None:
            if existing_competition.competition_id is None:
                raise ValueError(
                    "Der vorhandene Wettbewerb besitzt keine ID."
                )

            return int(
                existing_competition.competition_id
            )

        competition = Competition(
            competition_id=None,
            league_id=league_id,
            season_id=season_id,
            name=normalized_name,
            active=active,
        )

        return self.add(
            competition
        )

    def update(
        self,
        competition: Competition,
    ) -> int:
        if competition.competition_id is None:
            raise ValueError(
                "Die Wettbewerbs-ID fehlt."
            )

        if competition.competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        if competition.league_id <= 0:
            raise ValueError(
                "Ungültige Liga-ID."
            )

        if competition.season_id <= 0:
            raise ValueError(
                "Ungültige Saison-ID."
            )

        normalized_name = competition.name.strip()

        if not normalized_name:
            raise ValueError(
                "Der Wettbewerbsname darf nicht leer sein."
            )

        self.cursor.execute(
            """
            UPDATE competitions
            SET
                league_id = ?,
                season_id = ?,
                name = ?,
                active = ?
            WHERE competition_id = ?
            """,
            (
                competition.league_id,
                competition.season_id,
                normalized_name,
                int(competition.active),
                competition.competition_id,
            ),
        )

        self.connection.commit()

        return self.cursor.rowcount

    def delete(
        self,
        competition_id: int,
    ) -> int:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM competitions
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        self.connection.commit()

        return self.cursor.rowcount

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
                clubs.name ASC,
                teams.team_number ASC,
                teams.name ASC
            """
        )

        return self.cursor.fetchall()

    def get_competition_team_ids(
        self,
        competition_id: int,
    ) -> list[int]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        self.cursor.execute(
            """
            SELECT team_id
            FROM competition_teams
            WHERE competition_id = ?
            ORDER BY team_id ASC
            """,
            (competition_id,),
        )

        return [
            int(row[0])
            for row in self.cursor.fetchall()
        ]

    def get_competition_teams(
        self,
        competition_id: int,
    ) -> list[tuple]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

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
                clubs.name ASC,
                teams.team_number ASC,
                teams.name ASC
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def add_team(
        self,
        competition_id: int,
        team_id: int,
    ) -> bool:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        self.cursor.execute(
            """
            SELECT 1
            FROM competition_teams
            WHERE
                competition_id = ?
                AND team_id = ?
            LIMIT 1
            """,
            (
                competition_id,
                team_id,
            ),
        )

        if self.cursor.fetchone() is not None:
            return False

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

        return True

    def set_competition_teams(
        self,
        competition_id: int,
        team_ids: list[int],
    ) -> None:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        normalized_team_ids = sorted(
            {
                team_id
                for team_id in team_ids
                if team_id > 0
            }
        )

        try:
            self.cursor.execute(
                """
                DELETE FROM competition_teams
                WHERE competition_id = ?
                """,
                (competition_id,),
            )

            self.cursor.executemany(
                """
                INSERT INTO competition_teams (
                    competition_id,
                    team_id
                )
                VALUES (?, ?)
                """,
                [
                    (
                        competition_id,
                        team_id,
                    )
                    for team_id in normalized_team_ids
                ],
            )

            self.connection.commit()

        except sqlite3.Error:
            self.connection.rollback()
            raise

    @staticmethod
    def _create_competition(
        row: sqlite3.Row | tuple,
    ) -> Competition:
        return Competition(
            competition_id=row[0],
            league_id=row[1],
            season_id=row[2],
            name=row[3],
            active=bool(row[4]),
        )