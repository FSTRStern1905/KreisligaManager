import sqlite3

from src.database.models.match import Match


class MatchRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_by_id(self, match_id: int) -> Match | None:
        self.cursor.execute(
            """
            SELECT
                m.match_id,
                m.competition_id,
                m.season_id,
                m.league_id,
                m.matchday,
                m.match_date,
                m.kickoff_time,
                m.home_team_id,
                m.away_team_id,
                m.stadium_id,
                m.referee_id,
                m.attendance,
                m.home_goals,
                m.away_goals,
                m.status,
                m.notes,
                home_team.name,
                away_team.name
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE m.match_id = ?
            """,
            (match_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return self._row_to_match(row)

    def get_by_competition(
        self,
        competition_id: int,
    ) -> list[Match]:
        self.cursor.execute(
            """
            SELECT
                m.match_id,
                m.competition_id,
                m.season_id,
                m.league_id,
                m.matchday,
                m.match_date,
                m.kickoff_time,
                m.home_team_id,
                m.away_team_id,
                m.stadium_id,
                m.referee_id,
                m.attendance,
                m.home_goals,
                m.away_goals,
                m.status,
                m.notes,
                home_team.name,
                away_team.name
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE m.competition_id = ?
            ORDER BY
                m.matchday,
                m.match_date,
                m.kickoff_time,
                m.match_id
            """,
            (competition_id,),
        )

        return [
            self._row_to_match(row)
            for row in self.cursor.fetchall()
        ]

    def update(self, match: Match):
        if match.match_id is None:
            raise ValueError("Das Spiel besitzt keine match_id.")

        self.cursor.execute(
            """
            UPDATE matches
            SET
                competition_id = ?,
                season_id = ?,
                league_id = ?,
                matchday = ?,
                match_date = ?,
                kickoff_time = ?,
                home_team_id = ?,
                away_team_id = ?,
                stadium_id = ?,
                referee_id = ?,
                attendance = ?,
                home_goals = ?,
                away_goals = ?,
                status = ?,
                notes = ?
            WHERE match_id = ?
            """,
            (
                match.competition_id,
                match.season_id,
                match.league_id,
                match.matchday,
                match.match_date,
                match.kickoff_time,
                match.home_team_id,
                match.away_team_id,
                match.stadium_id,
                match.referee_id,
                match.attendance,
                match.home_goals,
                match.away_goals,
                match.status,
                match.notes,
                match.match_id,
            ),
        )

        self.connection.commit()

    def get_all_stadiums(self) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                stadium_id,
                name
            FROM stadiums
            ORDER BY name
            """
        )

        return self.cursor.fetchall()

    def get_all_referees(self) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                referee_id,
                TRIM(
                    COALESCE(first_name, '')
                    || ' '
                    || last_name
                ) AS full_name
            FROM referees
            ORDER BY
                last_name,
                first_name
            """
        )

        return self.cursor.fetchall()

    def get_match_count(
        self,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        return self.cursor.fetchone()[0]

    def get_finished_match_count(
        self,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
            """,
            (competition_id,),
        )

        return self.cursor.fetchone()[0]

    def get_open_match_count(
        self,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE
                competition_id = ?
                AND status <> 'finished'
            """,
            (competition_id,),
        )

        return self.cursor.fetchone()[0]

    def delete(self, match_id: int):
        self.cursor.execute(
            """
            DELETE FROM matches
            WHERE match_id = ?
            """,
            (match_id,),
        )

        self.connection.commit()

    def _row_to_match(self, row: tuple) -> Match:
        return Match(
            match_id=row[0],
            competition_id=row[1],
            season_id=row[2],
            league_id=row[3],
            matchday=row[4],
            match_date=row[5],
            kickoff_time=row[6],
            home_team_id=row[7],
            away_team_id=row[8],
            stadium_id=row[9],
            referee_id=row[10],
            attendance=row[11],
            home_goals=row[12],
            away_goals=row[13],
            status=row[14],
            notes=row[15] or "",
            home_team_name=row[16],
            away_team_name=row[17],
        )