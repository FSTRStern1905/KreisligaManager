import sqlite3


class EventRepository:

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.cursor = connection.cursor()

    def get(
        self,
        event_id: int,
    ) -> dict | None:
        if event_id <= 0:
            raise ValueError(
                "Ungültige Ereignis-ID."
            )

        self.cursor.execute(
            """
            SELECT
                events.*,
                event_types.code AS event_type_code,
                event_types.name AS event_type_name
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            WHERE events.event_id = ?
            LIMIT 1
            """,
            (event_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def get_by_match(
        self,
        match_id: int,
    ) -> list[dict]:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            """
            SELECT
                events.*,
                event_types.code AS event_type_code,
                event_types.name AS event_type_name
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            WHERE events.match_id = ?
            ORDER BY
                events.minute ASC,
                events.second ASC,
                events.event_id ASC
            """,
            (match_id,),
        )

        return [
            dict(row)
            for row in self.cursor.fetchall()
        ]

    def get_event_type_id(
        self,
        code: str,
    ) -> int | None:
        normalized_code = code.strip().upper()

        if not normalized_code:
            return None

        self.cursor.execute(
            """
            SELECT event_type_id
            FROM event_types
            WHERE code = ? COLLATE NOCASE
            LIMIT 1
            """,
            (normalized_code,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return int(row[0])

    def add(
        self,
        match_id: int,
        event_type_id: int,
        minute: int | None = None,
        second: int = 0,
        team_id: int | None = None,
        player_id: int | None = None,
        related_player_id: int | None = None,
        value: str = "",
        notes: str = "",
        commit: bool = True,
    ) -> int:
        self._validate_values(
            match_id=match_id,
            event_type_id=event_type_id,
            minute=minute,
            second=second,
            team_id=team_id,
            player_id=player_id,
            related_player_id=related_player_id,
        )

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
                value.strip(),
                notes.strip(),
            ),
        )

        if commit:
            self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def add_by_code(
        self,
        match_id: int,
        event_type_code: str,
        minute: int | None = None,
        second: int = 0,
        team_id: int | None = None,
        player_id: int | None = None,
        related_player_id: int | None = None,
        value: str = "",
        notes: str = "",
        commit: bool = True,
    ) -> int:
        event_type_id = self.get_event_type_id(
            event_type_code
        )

        if event_type_id is None:
            raise ValueError(
                "Unbekannter Ereignistyp: "
                f"{event_type_code}"
            )

        return self.add(
            match_id=match_id,
            event_type_id=event_type_id,
            minute=minute,
            second=second,
            team_id=team_id,
            player_id=player_id,
            related_player_id=related_player_id,
            value=value,
            notes=notes,
            commit=commit,
        )

    def delete(
        self,
        event_id: int,
        commit: bool = True,
    ) -> int:
        if event_id <= 0:
            raise ValueError(
                "Ungültige Ereignis-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM events
            WHERE event_id = ?
            """,
            (event_id,),
        )

        if commit:
            self.connection.commit()

        return self.cursor.rowcount

    def delete_by_match(
        self,
        match_id: int,
        commit: bool = True,
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM events
            WHERE match_id = ?
            """,
            (match_id,),
        )

        if commit:
            self.connection.commit()

        return self.cursor.rowcount

    def replace_match_events(
        self,
        match_id: int,
        events: list[dict],
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        try:
            self.delete_by_match(
                match_id=match_id,
                commit=False,
            )

            inserted_count = 0

            for event in events:
                event_type_id = event.get(
                    "event_type_id"
                )

                event_type_code = str(
                    event.get(
                        "event_type_code",
                        "",
                    )
                ).strip()

                if event_type_id is None:
                    event_type_id = (
                        self.get_event_type_id(
                            event_type_code
                        )
                    )

                if event_type_id is None:
                    raise ValueError(
                        "Ereignistyp konnte nicht "
                        "ermittelt werden: "
                        f"{event_type_code}"
                    )

                self.add(
                    match_id=match_id,
                    event_type_id=int(
                        event_type_id
                    ),
                    minute=event.get("minute"),
                    second=int(
                        event.get("second", 0)
                        or 0
                    ),
                    team_id=event.get("team_id"),
                    player_id=event.get(
                        "player_id"
                    ),
                    related_player_id=event.get(
                        "related_player_id"
                    ),
                    value=str(
                        event.get("value", "")
                        or ""
                    ),
                    notes=str(
                        event.get("notes", "")
                        or ""
                    ),
                    commit=False,
                )

                inserted_count += 1

            self.connection.commit()

            return inserted_count

        except Exception:
            self.connection.rollback()
            raise

    def count_by_match(
        self,
        match_id: int,
    ) -> int:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM events
            WHERE match_id = ?
            """,
            (match_id,),
        )

        return int(
            self.cursor.fetchone()[0]
        )

    @staticmethod
    def _validate_values(
        match_id: int,
        event_type_id: int,
        minute: int | None,
        second: int,
        team_id: int | None,
        player_id: int | None,
        related_player_id: int | None,
    ) -> None:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        if event_type_id <= 0:
            raise ValueError(
                "Ungültige Ereignistyp-ID."
            )

        if minute is not None and minute < 0:
            raise ValueError(
                "Die Spielminute darf nicht "
                "negativ sein."
            )

        if second < 0 or second > 59:
            raise ValueError(
                "Die Sekunde muss zwischen "
                "0 und 59 liegen."
            )

        optional_ids = {
            "Mannschafts-ID": team_id,
            "Spieler-ID": player_id,
            "Zugehörige Spieler-ID":
                related_player_id,
        }

        for name, value in optional_ids.items():
            if value is not None and value <= 0:
                raise ValueError(
                    f"Ungültige {name}."
                )