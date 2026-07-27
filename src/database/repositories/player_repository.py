import sqlite3


class PlayerRepository:
    COLUMNS = """
        player_id,
        external_id,
        team_id,
        first_name,
        last_name,
        birthdate,
        position,
        shirt_number,
        foot,
        height_cm,
        weight_kg,
        nationality,
        is_active
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

        self._ensure_external_id_column()
        self._ensure_indexes()

    def get(
        self,
        player_id: int,
    ) -> dict | None:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM players
            WHERE player_id = ?
            LIMIT 1
            """,
            (player_id,),
        )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def get_by_external_id(
        self,
        external_id: str,
    ) -> dict | None:
        normalized_external_id = (
            external_id.strip()
        )

        if not normalized_external_id:
            return None

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM players
            WHERE external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def get_by_name_and_team(
        self,
        team_id: int | None,
        first_name: str,
        last_name: str,
    ) -> dict | None:
        normalized_first_name = (
            first_name.strip()
        )
        normalized_last_name = (
            last_name.strip()
        )

        if not normalized_last_name:
            return None

        if team_id is None:
            self.cursor.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM players
                WHERE
                    team_id IS NULL
                    AND first_name = ?
                        COLLATE NOCASE
                    AND last_name = ?
                        COLLATE NOCASE
                LIMIT 1
                """,
                (
                    normalized_first_name,
                    normalized_last_name,
                ),
            )
        else:
            if team_id <= 0:
                raise ValueError(
                    "Ungültige Mannschafts-ID."
                )

            self.cursor.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM players
                WHERE
                    team_id = ?
                    AND first_name = ?
                        COLLATE NOCASE
                    AND last_name = ?
                        COLLATE NOCASE
                LIMIT 1
                """,
                (
                    team_id,
                    normalized_first_name,
                    normalized_last_name,
                ),
            )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def get_by_team(
        self,
        team_id: int,
        active_only: bool = False,
    ) -> list[dict]:
        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        active_condition = ""

        if active_only:
            active_condition = """
                AND is_active = 1
            """

        self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM players
            WHERE team_id = ?
            {active_condition}
            ORDER BY
                last_name COLLATE NOCASE,
                first_name COLLATE NOCASE
            """,
            (team_id,),
        )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def search(
        self,
        search_text: str,
        team_id: int | None = None,
    ) -> list[dict]:
        normalized_search = (
            search_text.strip()
        )

        if not normalized_search:
            return []

        search_value = (
            f"%{normalized_search}%"
        )

        if team_id is None:
            self.cursor.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM players
                WHERE
                    first_name LIKE ?
                        COLLATE NOCASE
                    OR last_name LIKE ?
                        COLLATE NOCASE
                    OR (
                        first_name || ' ' ||
                        last_name
                    ) LIKE ? COLLATE NOCASE
                ORDER BY
                    last_name COLLATE NOCASE,
                    first_name COLLATE NOCASE
                """,
                (
                    search_value,
                    search_value,
                    search_value,
                ),
            )
        else:
            if team_id <= 0:
                raise ValueError(
                    "Ungültige Mannschafts-ID."
                )

            self.cursor.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM players
                WHERE
                    team_id = ?
                    AND (
                        first_name LIKE ?
                            COLLATE NOCASE
                        OR last_name LIKE ?
                            COLLATE NOCASE
                        OR (
                            first_name || ' ' ||
                            last_name
                        ) LIKE ? COLLATE NOCASE
                    )
                ORDER BY
                    last_name COLLATE NOCASE,
                    first_name COLLATE NOCASE
                """,
                (
                    team_id,
                    search_value,
                    search_value,
                    search_value,
                ),
            )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def add(
        self,
        first_name: str,
        last_name: str,
        team_id: int | None = None,
        external_id: str = "",
        birthdate: str = "",
        position: str = "",
        shirt_number: int | None = None,
        foot: str = "",
        height_cm: int | None = None,
        weight_kg: int | None = None,
        nationality: str = "Deutschland",
        is_active: bool = True,
        commit: bool = True,
    ) -> int:
        normalized_values = (
            self._validate_and_normalize(
                first_name=first_name,
                last_name=last_name,
                team_id=team_id,
                external_id=external_id,
                shirt_number=shirt_number,
                height_cm=height_cm,
                weight_kg=weight_kg,
            )
        )

        self.cursor.execute(
            """
            INSERT INTO players (
                external_id,
                team_id,
                first_name,
                last_name,
                birthdate,
                position,
                shirt_number,
                foot,
                height_cm,
                weight_kg,
                nationality,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_values[
                    "external_id"
                ],
                team_id,
                normalized_values[
                    "first_name"
                ],
                normalized_values[
                    "last_name"
                ],
                birthdate.strip(),
                position.strip(),
                shirt_number,
                foot.strip(),
                height_cm,
                weight_kg,
                (
                    nationality.strip()
                    or "Deutschland"
                ),
                int(is_active),
            ),
        )

        if commit:
            self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def update(
        self,
        player_id: int,
        first_name: str,
        last_name: str,
        team_id: int | None = None,
        external_id: str = "",
        birthdate: str = "",
        position: str = "",
        shirt_number: int | None = None,
        foot: str = "",
        height_cm: int | None = None,
        weight_kg: int | None = None,
        nationality: str = "Deutschland",
        is_active: bool = True,
        commit: bool = True,
    ) -> None:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        normalized_values = (
            self._validate_and_normalize(
                first_name=first_name,
                last_name=last_name,
                team_id=team_id,
                external_id=external_id,
                shirt_number=shirt_number,
                height_cm=height_cm,
                weight_kg=weight_kg,
            )
        )

        self.cursor.execute(
            """
            UPDATE players
            SET
                external_id = ?,
                team_id = ?,
                first_name = ?,
                last_name = ?,
                birthdate = ?,
                position = ?,
                shirt_number = ?,
                foot = ?,
                height_cm = ?,
                weight_kg = ?,
                nationality = ?,
                is_active = ?
            WHERE player_id = ?
            """,
            (
                normalized_values[
                    "external_id"
                ],
                team_id,
                normalized_values[
                    "first_name"
                ],
                normalized_values[
                    "last_name"
                ],
                birthdate.strip(),
                position.strip(),
                shirt_number,
                foot.strip(),
                height_cm,
                weight_kg,
                (
                    nationality.strip()
                    or "Deutschland"
                ),
                int(is_active),
                player_id,
            ),
        )

        if self.cursor.rowcount == 0:
            raise ValueError(
                "Spieler wurde nicht gefunden."
            )

        if commit:
            self.connection.commit()

    def upsert(
        self,
        first_name: str,
        last_name: str,
        team_id: int | None = None,
        external_id: str = "",
        birthdate: str = "",
        position: str = "",
        shirt_number: int | None = None,
        foot: str = "",
        height_cm: int | None = None,
        weight_kg: int | None = None,
        nationality: str = "Deutschland",
        is_active: bool = True,
        commit: bool = True,
    ) -> int:
        normalized_external_id = (
            external_id.strip()
        )

        existing = None

        if normalized_external_id:
            existing = (
                self.get_by_external_id(
                    normalized_external_id
                )
            )

        if existing is None:
            existing = (
                self.get_by_name_and_team(
                    team_id=team_id,
                    first_name=first_name,
                    last_name=last_name,
                )
            )

        if existing is None:
            return self.add(
                first_name=first_name,
                last_name=last_name,
                team_id=team_id,
                external_id=normalized_external_id,
                birthdate=birthdate,
                position=position,
                shirt_number=shirt_number,
                foot=foot,
                height_cm=height_cm,
                weight_kg=weight_kg,
                nationality=nationality,
                is_active=is_active,
                commit=commit,
            )

        player_id = int(
            existing["player_id"]
        )

        self.update(
            player_id=player_id,
            first_name=(
                first_name
                or existing["first_name"]
                or ""
            ),
            last_name=(
                last_name
                or existing["last_name"]
            ),
            team_id=(
                team_id
                if team_id is not None
                else existing["team_id"]
            ),
            external_id=(
                normalized_external_id
                or existing["external_id"]
                or ""
            ),
            birthdate=(
                birthdate
                or existing["birthdate"]
                or ""
            ),
            position=(
                position
                or existing["position"]
                or ""
            ),
            shirt_number=(
                shirt_number
                if shirt_number is not None
                else existing["shirt_number"]
            ),
            foot=(
                foot
                or existing["foot"]
                or ""
            ),
            height_cm=(
                height_cm
                if height_cm is not None
                else existing["height_cm"]
            ),
            weight_kg=(
                weight_kg
                if weight_kg is not None
                else existing["weight_kg"]
            ),
            nationality=(
                nationality
                or existing["nationality"]
                or "Deutschland"
            ),
            is_active=is_active,
            commit=commit,
        )

        return player_id

    def get_or_create(
        self,
        first_name: str,
        last_name: str,
        team_id: int | None = None,
        external_id: str = "",
        commit: bool = True,
    ) -> int:
        normalized_external_id = (
            external_id.strip()
        )

        existing = None

        if normalized_external_id:
            existing = (
                self.get_by_external_id(
                    normalized_external_id
                )
            )

        if existing is None:
            existing = (
                self.get_by_name_and_team(
                    team_id=team_id,
                    first_name=first_name,
                    last_name=last_name,
                )
            )

        if existing is not None:
            player_id = int(
                existing["player_id"]
            )

            should_update = (
                normalized_external_id
                and not existing["external_id"]
            )

            if should_update:
                self.cursor.execute(
                    """
                    UPDATE players
                    SET external_id = ?
                    WHERE player_id = ?
                    """,
                    (
                        normalized_external_id,
                        player_id,
                    ),
                )

                if commit:
                    self.connection.commit()

            return player_id

        return self.add(
            first_name=first_name,
            last_name=last_name,
            team_id=team_id,
            external_id=normalized_external_id,
            commit=commit,
        )

    def delete(
        self,
        player_id: int,
        commit: bool = True,
    ) -> int:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM players
            WHERE player_id = ?
            """,
            (player_id,),
        )

        if commit:
            self.connection.commit()

        return self.cursor.rowcount

    def set_active(
        self,
        player_id: int,
        is_active: bool,
        commit: bool = True,
    ) -> None:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        self.cursor.execute(
            """
            UPDATE players
            SET is_active = ?
            WHERE player_id = ?
            """,
            (
                int(is_active),
                player_id,
            ),
        )

        if self.cursor.rowcount == 0:
            raise ValueError(
                "Spieler wurde nicht gefunden."
            )

        if commit:
            self.connection.commit()

    def _ensure_external_id_column(
        self,
    ) -> None:
        self.cursor.execute(
            "PRAGMA table_info(players)"
        )

        columns = {
            row[1]
            for row in self.cursor.fetchall()
        }

        if "external_id" not in columns:
            self.cursor.execute(
                """
                ALTER TABLE players
                ADD COLUMN external_id TEXT
                """
            )

            self.connection.commit()

    def _ensure_indexes(
        self,
    ) -> None:
        self.cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_players_external_id
            ON players(external_id)
            WHERE
                external_id IS NOT NULL
                AND external_id != ''
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_players_team_name
            ON players(
                team_id,
                last_name,
                first_name
            )
            """
        )

        self.connection.commit()

    @staticmethod
    def _validate_and_normalize(
        first_name: str,
        last_name: str,
        team_id: int | None,
        external_id: str,
        shirt_number: int | None,
        height_cm: int | None,
        weight_kg: int | None,
    ) -> dict:
        normalized_first_name = (
            first_name.strip()
        )
        normalized_last_name = (
            last_name.strip()
        )
        normalized_external_id = (
            external_id.strip()
        )

        if not normalized_last_name:
            raise ValueError(
                "Der Nachname darf nicht leer sein."
            )

        if team_id is not None and team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        if (
            shirt_number is not None
            and shirt_number < 0
        ):
            raise ValueError(
                "Die Rückennummer darf nicht "
                "negativ sein."
            )

        if (
            height_cm is not None
            and height_cm <= 0
        ):
            raise ValueError(
                "Die Körpergröße muss größer "
                "als 0 sein."
            )

        if (
            weight_kg is not None
            and weight_kg <= 0
        ):
            raise ValueError(
                "Das Gewicht muss größer als "
                "0 sein."
            )

        return {
            "first_name":
                normalized_first_name,
            "last_name":
                normalized_last_name,
            "external_id":
                normalized_external_id
                or None,
        }

    @staticmethod
    def _row_to_dict(
        row,
    ) -> dict | None:
        if row is None:
            return None

        return {
            "player_id": row[0],
            "external_id": row[1],
            "team_id": row[2],
            "first_name": row[3],
            "last_name": row[4],
            "birthdate": row[5],
            "position": row[6],
            "shirt_number": row[7],
            "foot": row[8],
            "height_cm": row[9],
            "weight_kg": row[10],
            "nationality": row[11],
            "is_active": bool(row[12]),
        }