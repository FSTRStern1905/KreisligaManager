import sqlite3


class DemoEventGenerator:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def get_event_type_id(
        self,
        code: str,
    ) -> int:
        self.cursor.execute(
            """
            SELECT event_type_id
            FROM event_types
            WHERE code = ?
            """,
            (code,),
        )

        result = self.cursor.fetchone()

        if result is None:
            raise ValueError(
                f"Eventtyp '{code}' wurde nicht gefunden."
            )

        return result[0]

    def load_finished_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                match_id,
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday,
                match_id
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def load_active_players(
        self,
        team_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                player_id,
                position,
                shirt_number
            FROM players
            WHERE
                team_id = ?
                AND is_active = 1
            ORDER BY
                shirt_number,
                player_id
            """,
            (team_id,),
        )

        return self.cursor.fetchall()

    def delete_events(
        self,
        competition_id: int,
        event_type_codes: list[str],
    ):
        if not event_type_codes:
            return

        placeholders = ",".join(
            "?"
            for _ in event_type_codes
        )

        self.cursor.execute(
            f"""
            DELETE FROM events
            WHERE
                match_id IN (
                    SELECT match_id
                    FROM matches
                    WHERE competition_id = ?
                )
                AND event_type_id IN (
                    SELECT event_type_id
                    FROM event_types
                    WHERE code IN ({placeholders})
                )
            """,
            (
                competition_id,
                *event_type_codes,
            ),
        )

    def insert_event(
        self,
        match_id: int,
        event_type_id: int,
        minute: int,
        team_id: int | None,
        player_id: int | None,
        related_player_id: int | None = None,
        value: str | None = None,
        notes: str | None = None,
        second: int = 0,
    ) -> int:
        self.cursor.execute(
            """
            INSERT INTO events (
                match_id,
                event_type_id,
                minute,
                second,
                team_id,
                player_id,
                related_player_id,
                value,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                match_id,
                event_type_id,
                minute,
                second,
                team_id,
                player_id,
                related_player_id,
                value,
                notes,
            ),
        )

        return self.cursor.lastrowid

    def commit(self):
        self.connection.commit()