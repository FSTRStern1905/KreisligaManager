from src.database.repositories.base_repository import BaseRepository


class StandingRepository(BaseRepository):

    TABLE = "standings"
    ID = "standing_id"

    def get(
        self,
        standing_id: int,
    ) -> dict | None:
        if standing_id <= 0:
            raise ValueError(
                "Ungültige Tabellen-ID."
            )

        return self.fetch_by_id(
            self.TABLE,
            self.ID,
            standing_id,
        )

    def get_by_competition(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                standings.*,
                teams.name AS team_name,
                teams.short_name AS team_short_name
            FROM standings
            INNER JOIN teams
                ON teams.team_id = standings.team_id
            WHERE standings.competition_id = ?
            ORDER BY
                standings.position ASC,
                teams.name ASC
            """,
            (competition_id,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def get_by_competition_and_team(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict | None:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM standings
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

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def upsert(
        self,
        competition_id: int,
        team_id: int,
        position: int,
        played: int,
        wins: int,
        draws: int,
        losses: int,
        goals_for: int,
        goals_against: int,
        points: int,
        source: str = "fussball.de",
        commit: bool = True,
    ) -> int:
        self._validate_values(
            competition_id=competition_id,
            team_id=team_id,
            position=position,
            played=played,
            wins=wins,
            draws=draws,
            losses=losses,
            goals_for=goals_for,
            goals_against=goals_against,
            points=points,
        )

        goal_difference = (
            goals_for - goals_against
        )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO standings (
                competition_id,
                team_id,
                position,
                played,
                wins,
                draws,
                losses,
                goals_for,
                goals_against,
                goal_difference,
                points,
                source,
                imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (
                competition_id,
                team_id
            )
            DO UPDATE SET
                position = excluded.position,
                played = excluded.played,
                wins = excluded.wins,
                draws = excluded.draws,
                losses = excluded.losses,
                goals_for = excluded.goals_for,
                goals_against = excluded.goals_against,
                goal_difference = excluded.goal_difference,
                points = excluded.points,
                source = excluded.source,
                imported_at = CURRENT_TIMESTAMP
            """,
            (
                competition_id,
                team_id,
                position,
                played,
                wins,
                draws,
                losses,
                goals_for,
                goals_against,
                goal_difference,
                points,
                source.strip() or "fussball.de",
            ),
        )

        if commit:
            self.connection.commit()

        row = self.get_by_competition_and_team(
            competition_id=competition_id,
            team_id=team_id,
        )

        if row is None:
            raise RuntimeError(
                "Tabelleneintrag konnte nach dem Speichern "
                "nicht gefunden werden."
            )

        return int(
            row[self.ID]
        )

    def delete_by_competition(
        self,
        competition_id: int,
        commit: bool = True,
    ) -> int:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            DELETE FROM standings
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        if commit:
            self.connection.commit()

        return cursor.rowcount

    def count_by_competition(
        self,
        competition_id: int,
    ) -> int:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM standings
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        return int(
            cursor.fetchone()[0]
        )

    @staticmethod
    def _validate_values(
        competition_id: int,
        team_id: int,
        position: int,
        played: int,
        wins: int,
        draws: int,
        losses: int,
        goals_for: int,
        goals_against: int,
        points: int,
    ) -> None:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        if position <= 0:
            raise ValueError(
                "Der Tabellenplatz muss größer als 0 sein."
            )

        values = {
            "Spiele": played,
            "Siege": wins,
            "Unentschieden": draws,
            "Niederlagen": losses,
            "Tore": goals_for,
            "Gegentore": goals_against,
            "Punkte": points,
        }

        for name, value in values.items():
            if value < 0:
                raise ValueError(
                    f"{name} darf nicht negativ sein."
                )

        if wins + draws + losses != played:
            raise ValueError(
                "Siege, Unentschieden und Niederlagen "
                "müssen zusammen der Spielanzahl entsprechen."
            )
