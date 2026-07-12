import sqlite3

from src.demo.competition import DEMO_COMPETITION


class CompetitionGenerator:
    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor

    def generate(self) -> int:
        season_id = self._create_season()
        league_id = self._create_league()
        competition_id = self._create_competition(
            season_id=season_id,
            league_id=league_id,
        )

        return competition_id

    def _create_season(self) -> int:
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO seasons (
                name,
                start_date,
                end_date
            )
            VALUES (?, ?, ?)
            """,
            (
                DEMO_COMPETITION.season_name,
                DEMO_COMPETITION.season_start_date,
                DEMO_COMPETITION.season_end_date,
            ),
        )

        self.cursor.execute(
            """
            SELECT season_id
            FROM seasons
            WHERE name = ?
            """,
            (DEMO_COMPETITION.season_name,),
        )

        result = self.cursor.fetchone()

        if result is None:
            raise ValueError("Demo-Saison konnte nicht erzeugt werden.")

        return result[0]

    def _create_league(self) -> int:
        self.cursor.execute(
            """
            SELECT league_id
            FROM leagues
            WHERE name = ?
            ORDER BY league_id
            LIMIT 1
            """,
            (DEMO_COMPETITION.league_name,),
        )

        result = self.cursor.fetchone()

        if result is not None:
            return result[0]

        self.cursor.execute(
            """
            INSERT INTO leagues (
                name,
                level,
                season_type
            )
            VALUES (?, ?, ?)
            """,
            (
                DEMO_COMPETITION.league_name,
                DEMO_COMPETITION.league_level,
                DEMO_COMPETITION.league_type,
            ),
        )

        return self.cursor.lastrowid

    def _create_competition(
        self,
        season_id: int,
        league_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT competition_id
            FROM competitions
            WHERE
                name = ?
                AND season_id = ?
                AND league_id = ?
            ORDER BY competition_id
            LIMIT 1
            """,
            (
                DEMO_COMPETITION.competition_name,
                season_id,
                league_id,
            ),
        )

        result = self.cursor.fetchone()

        if result is not None:
            competition_id = result[0]

            self.cursor.execute(
                """
                UPDATE competitions
                SET active = 1
                WHERE competition_id = ?
                """,
                (competition_id,),
            )

            return competition_id

        self.cursor.execute(
            """
            INSERT INTO competitions (
                season_id,
                league_id,
                name,
                active
            )
            VALUES (?, ?, ?, 1)
            """,
            (
                season_id,
                league_id,
                DEMO_COMPETITION.competition_name,
            ),
        )

        return self.cursor.lastrowid