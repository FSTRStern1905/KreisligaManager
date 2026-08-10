import sqlite3

from src.database.models.match import Match


class MatchRepository:

    SELECT_FIELDS = """
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
        m.detail_imported,
        m.notes,
        m.external_id,
        home_team.name,
        away_team.name
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def get(
        self,
        match_id: int,
    ) -> Match | None:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            f"""
            SELECT
                {self.SELECT_FIELDS}
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE m.match_id = ?
            LIMIT 1
            """,
            (match_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return self._row_to_match(row)

    def get_by_id(
        self,
        match_id: int,
    ) -> Match | None:
        return self.get(match_id)

    def get_by_external_id(
        self,
        external_id: str,
    ) -> Match | None:
        normalized_external_id = external_id.strip()

        if not normalized_external_id:
            return None

        self.cursor.execute(
            f"""
            SELECT
                {self.SELECT_FIELDS}
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE m.external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return self._row_to_match(row)

    def get_by_competition(
        self,
        competition_id: int,
    ) -> list[Match]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        self.cursor.execute(
            f"""
            SELECT
                {self.SELECT_FIELDS}
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE m.competition_id = ?
            ORDER BY
                m.matchday ASC,
                m.match_date ASC,
                m.kickoff_time ASC,
                m.match_id ASC
            """,
            (competition_id,),
        )

        return [
            self._row_to_match(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_date(
        self,
        match_date: str,
    ) -> list[Match]:
        normalized_date = match_date.strip()

        if not normalized_date:
            raise ValueError(
                "Das Spieldatum darf nicht leer sein."
            )

        self.cursor.execute(
            f"""
            SELECT
                {self.SELECT_FIELDS}
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE m.match_date = ?
            ORDER BY
                m.kickoff_time ASC,
                m.match_id ASC
            """,
            (normalized_date,),
        )

        return [
            self._row_to_match(row)
            for row in self.cursor.fetchall()
        ]

    def get_between_dates(
        self,
        start_date: str,
        end_date: str,
    ) -> list[Match]:
        normalized_start_date = (
            start_date.strip()
        )
        normalized_end_date = (
            end_date.strip()
        )

        if not normalized_start_date:
            raise ValueError(
                "Das Startdatum darf nicht leer sein."
            )

        if not normalized_end_date:
            raise ValueError(
                "Das Enddatum darf nicht leer sein."
            )

        if normalized_start_date > normalized_end_date:
            raise ValueError(
                "Das Startdatum darf nicht nach dem Enddatum liegen."
            )

        self.cursor.execute(
            f"""
            SELECT
                {self.SELECT_FIELDS}
            FROM matches AS m
            INNER JOIN teams AS home_team
                ON home_team.team_id = m.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = m.away_team_id
            WHERE
                m.match_date >= ?
                AND m.match_date <= ?
            ORDER BY
                m.match_date ASC,
                m.kickoff_time ASC,
                m.match_id ASC
            """,
            (
                normalized_start_date,
                normalized_end_date,
            ),
        )

        return [
            self._row_to_match(row)
            for row in self.cursor.fetchall()
        ]

    def add(
        self,
        match: Match,
    ) -> int:
        self._validate_match(match)

        normalized_external_id = (
            match.external_id.strip()
            if match.external_id
            else None
        )

        self.cursor.execute(
            """
            INSERT INTO matches (
                competition_id,
                season_id,
                league_id,
                matchday,
                match_date,
                kickoff_time,
                home_team_id,
                away_team_id,
                stadium_id,
                referee_id,
                attendance,
                home_goals,
                away_goals,
                status,
                detail_imported,
                notes,
                external_id
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
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
                match.status.strip(),
            int(match.detail_imported),
                match.notes.strip(),
                normalized_external_id,
            ),
        )

        self.connection.commit()

        return int(self.cursor.lastrowid)

    def update(
        self,
        match: Match,
    ) -> int:
        if match.match_id is None:
            raise ValueError(
                "Das Spiel besitzt keine match_id."
            )

        if match.match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self._validate_match(match)

        normalized_external_id = (
            match.external_id.strip()
            if match.external_id
            else None
        )

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
                detail_imported = ?,
                notes = ?,
                external_id = ?
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
                match.status.strip(),
            int(match.detail_imported),
                match.notes.strip(),
                normalized_external_id,
                match.match_id,
            ),
        )

        self.connection.commit()

        return self.cursor.rowcount

    def upsert(
        self,
        match: Match,
    ) -> tuple[int, bool]:
        normalized_external_id = (
            match.external_id.strip()
            if match.external_id
            else ""
        )

        if not normalized_external_id:
            match_id = self.add(match)

            return match_id, True

        existing_match = self.get_by_external_id(
            normalized_external_id
        )

        if existing_match is None:
            match.external_id = normalized_external_id

            match_id = self.add(match)

            return match_id, True

        if existing_match.match_id is None:
            raise ValueError(
                "Das vorhandene Spiel besitzt keine match_id."
            )

        match.match_id = existing_match.match_id
        match.external_id = normalized_external_id

        self.update(match)

        return existing_match.match_id, False

    def delete(
        self,
        match_id: int,
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM matches
            WHERE match_id = ?
            """,
            (match_id,),
        )

        self.connection.commit()

        return self.cursor.rowcount

    def get_all_stadiums(self) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                stadium_id,
                name
            FROM stadiums
            ORDER BY name ASC
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
                    || COALESCE(last_name, '')
                ) AS full_name
            FROM referees
            ORDER BY
                last_name ASC,
                first_name ASC
            """
        )

        return self.cursor.fetchall()

    def get_match_count(
        self,
        competition_id: int,
    ) -> int:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        return int(row[0])

    def get_finished_match_count(
        self,
        competition_id: int,
    ) -> int:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

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

        row = self.cursor.fetchone()

        return int(row[0])

    def get_open_match_count(
        self,
        competition_id: int,
    ) -> int:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

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

        row = self.cursor.fetchone()

        return int(row[0])

    @staticmethod
    def _validate_match(
        match: Match,
    ) -> None:
        if match.season_id is None or match.season_id <= 0:
            raise ValueError(
                "Ungültige Saison-ID."
            )

        if (
            match.competition_id is not None
            and match.competition_id <= 0
        ):
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        if (
            match.league_id is not None
            and match.league_id <= 0
        ):
            raise ValueError(
                "Ungültige Liga-ID."
            )

        if (
            match.home_team_id is None
            or match.home_team_id <= 0
        ):
            raise ValueError(
                "Ungültige Heim-Mannschafts-ID."
            )

        if (
            match.away_team_id is None
            or match.away_team_id <= 0
        ):
            raise ValueError(
                "Ungültige Auswärts-Mannschafts-ID."
            )

        if match.home_team_id == match.away_team_id:
            raise ValueError(
                "Heim- und Auswärtsmannschaft dürfen nicht identisch sein."
            )

        if (
            match.matchday is not None
            and match.matchday <= 0
        ):
            raise ValueError(
                "Der Spieltag muss größer als 0 sein."
            )

        if (
            match.attendance is not None
            and match.attendance < 0
        ):
            raise ValueError(
                "Die Zuschauerzahl darf nicht negativ sein."
            )

        if (
            match.home_goals is not None
            and match.home_goals < 0
        ):
            raise ValueError(
                "Die Heimtore dürfen nicht negativ sein."
            )

        if (
            match.away_goals is not None
            and match.away_goals < 0
        ):
            raise ValueError(
                "Die Auswärtstore dürfen nicht negativ sein."
            )

        if not match.status.strip():
            raise ValueError(
                "Der Spielstatus darf nicht leer sein."
            )

    @staticmethod
    def _row_to_match(
        row: sqlite3.Row | tuple,
    ) -> Match:
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
            detail_imported=bool(row[15]),
            notes=row[16] or "",
            external_id=row[17] or "",
            home_team_name=row[18],
            away_team_name=row[19],
        )