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
        self._ensure_external_id_alias_table()
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

        player = self._row_to_dict(
            self.cursor.fetchone()
        )

        if player is not None:
            return player

        self.cursor.execute(
            f"""
            SELECT
                {", ".join(
                    f"players.{column.strip()}"
                    for column in self.COLUMNS.split(",")
                )}
            FROM player_external_ids
            INNER JOIN players
                ON players.player_id =
                   player_external_ids.player_id
            WHERE
                player_external_ids.external_id = ?
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

        player_id = int(
            self.cursor.lastrowid
        )

        external_id_value = (
            normalized_values["external_id"]
        )

        if external_id_value:
            self._add_external_id_alias(
                player_id=player_id,
                external_id=external_id_value,
                source="primary",
                commit=False,
            )

        if commit:
            self.connection.commit()

        return player_id

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

        external_id_value = (
            normalized_values["external_id"]
        )

        if external_id_value:
            self._add_external_id_alias(
                player_id=player_id,
                external_id=external_id_value,
                source="primary",
                commit=False,
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
                self._choose_preferred_last_name(
                    incoming_last_name=last_name,
                    existing_last_name=(
                        existing["last_name"]
                        or ""
                    ),
                    incoming_external_id=(
                        normalized_external_id
                    ),
                )
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
        normalized_first_name = (
            first_name.strip()
        )
        normalized_last_name = (
            last_name.strip()
        )
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
                    first_name=normalized_first_name,
                    last_name=normalized_last_name,
                )
            )

        if (
            existing is None
            and not self._is_unknown_placeholder(
                normalized_last_name,
                normalized_external_id,
            )
        ):
            existing = (
                self._find_compatible_player(
                    team_id=team_id,
                    first_name=normalized_first_name,
                    last_name=normalized_last_name,
                )
            )

        if existing is not None:
            player_id = int(
                existing["player_id"]
            )

            if normalized_external_id:
                self._add_external_id_alias(
                    player_id=player_id,
                    external_id=normalized_external_id,
                    source="fussball.de",
                    commit=False,
                )

            existing_first_name = (
                existing["first_name"]
                or ""
            ).strip()
            existing_last_name = (
                existing["last_name"]
                or ""
            ).strip()

            incoming_is_placeholder = (
                self._is_unknown_placeholder(
                    normalized_last_name,
                    normalized_external_id,
                )
            )
            existing_is_placeholder = (
                self._is_unknown_placeholder(
                    existing_last_name,
                    existing["external_id"] or "",
                )
            )

            should_update_primary_id = bool(
                normalized_external_id
                and not existing["external_id"]
            )

            should_update_first_name = bool(
                normalized_first_name
                and (
                    not existing_first_name
                    or existing_is_placeholder
                )
                and not incoming_is_placeholder
            )

            should_update_last_name = bool(
                normalized_last_name
                and existing_is_placeholder
                and not incoming_is_placeholder
            )

            if (
                should_update_primary_id
                or should_update_first_name
                or should_update_last_name
            ):
                self.cursor.execute(
                    """
                    UPDATE players
                    SET
                        external_id = CASE
                            WHEN
                                (external_id IS NULL
                                 OR external_id = '')
                                AND ? != ''
                            THEN ?
                            ELSE external_id
                        END,
                        first_name = CASE
                            WHEN ? = 1
                            THEN ?
                            ELSE first_name
                        END,
                        last_name = CASE
                            WHEN ? = 1
                            THEN ?
                            ELSE last_name
                        END
                    WHERE player_id = ?
                    """,
                    (
                        normalized_external_id,
                        normalized_external_id,
                        int(should_update_first_name),
                        normalized_first_name,
                        int(should_update_last_name),
                        normalized_last_name,
                        player_id,
                    ),
                )

            if commit:
                self.connection.commit()

            return player_id

        return self.add(
            first_name=normalized_first_name,
            last_name=normalized_last_name,
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

    @classmethod
    def _choose_preferred_last_name(
        cls,
        incoming_last_name: str,
        existing_last_name: str,
        incoming_external_id: str = "",
    ) -> str:
        normalized_incoming = (
            incoming_last_name.strip()
        )
        normalized_existing = (
            existing_last_name.strip()
        )

        if not normalized_incoming:
            return normalized_existing

        incoming_is_placeholder = (
            cls._is_unknown_placeholder(
                normalized_incoming,
                incoming_external_id,
            )
        )
        existing_is_placeholder = (
            cls._is_unknown_placeholder(
                normalized_existing
            )
        )

        if (
            incoming_is_placeholder
            and normalized_existing
            and not existing_is_placeholder
        ):
            return normalized_existing

        return normalized_incoming

    @staticmethod
    def _is_unknown_placeholder(
        last_name: str,
        external_id: str = "",
    ) -> bool:
        normalized_last_name = (
            " ".join(
                last_name.strip().split()
            )
        )

        if not normalized_last_name:
            return False

        normalized_external_id = (
            external_id.strip()
        )

        if normalized_external_id:
            return (
                normalized_last_name.casefold()
                == (
                    "Unbekannt "
                    f"{normalized_external_id}"
                ).casefold()
            )

        return (
            normalized_last_name.casefold()
            .startswith("unbekannt ")
        )

    def _find_compatible_player(
        self,
        team_id: int | None,
        first_name: str,
        last_name: str,
    ) -> dict | None:
        """
        Vorsichtiges Fallback-Matching.

        Ein Spieler wird nur zusammengeführt, wenn:
        - Mannschaft und Nachname übereinstimmen,
        - genau ein plausibler Kandidat existiert,
        - und die Vornamen gleich sind oder auf einer
          Seite fehlen.

        Dadurch wird z. B. "Bahoya" aus der Aufstellung
        mit "Jean-Mattéo Bahoya" aus dem Liveticker
        zusammengeführt, ohne beliebige Namensähnlichkeit
        automatisch zu akzeptieren.
        """
        normalized_last_name = (
            self._normalize_name_for_match(
                last_name
            )
        )
        normalized_first_name = (
            self._normalize_name_for_match(
                first_name
            )
        )

        if not normalized_last_name:
            return None

        if team_id is None:
            self.cursor.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM players
                WHERE team_id IS NULL
                ORDER BY player_id
                """
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
                WHERE team_id = ?
                ORDER BY player_id
                """,
                (team_id,),
            )

        candidates: list[dict] = []

        for row in self.cursor.fetchall():
            candidate = self._row_to_dict(
                row
            )

            if candidate is None:
                continue

            candidate_last_name = (
                self._normalize_name_for_match(
                    candidate["last_name"]
                    or ""
                )
            )

            if (
                candidate_last_name
                != normalized_last_name
            ):
                continue

            candidate_first_name = (
                self._normalize_name_for_match(
                    candidate["first_name"]
                    or ""
                )
            )

            if (
                not normalized_first_name
                or not candidate_first_name
                or candidate_first_name
                    == normalized_first_name
            ):
                candidates.append(
                    candidate
                )

        if len(candidates) != 1:
            return None

        return candidates[0]

    def _add_external_id_alias(
        self,
        player_id: int,
        external_id: str,
        source: str = "fussball.de",
        commit: bool = True,
    ) -> None:
        normalized_external_id = (
            external_id.strip()
        )

        if (
            player_id <= 0
            or not normalized_external_id
        ):
            return

        existing = self.cursor.execute(
            """
            SELECT player_id
            FROM player_external_ids
            WHERE external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        ).fetchone()

        if existing is not None:
            existing_player_id = int(
                existing[0]
            )

            if existing_player_id != player_id:
                raise ValueError(
                    "Externe Spieler-ID ist bereits "
                    "einem anderen Spieler zugeordnet: "
                    f"{normalized_external_id}"
                )

            return

        self.cursor.execute(
            """
            INSERT INTO player_external_ids (
                player_id,
                external_id,
                source
            )
            VALUES (?, ?, ?)
            """,
            (
                player_id,
                normalized_external_id,
                source.strip()
                or "fussball.de",
            ),
        )

        if commit:
            self.connection.commit()

    def _ensure_external_id_alias_table(
        self,
    ) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS
                player_external_ids (
                    player_external_id_id
                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id
                        INTEGER NOT NULL,
                    external_id
                        TEXT NOT NULL UNIQUE,
                    source
                        TEXT NOT NULL DEFAULT 'fussball.de',
                    created_at
                        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id)
                        REFERENCES players(player_id)
                        ON DELETE CASCADE
                )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_player_external_ids_player
            ON player_external_ids(player_id)
            """
        )

        self.cursor.execute(
            """
            INSERT OR IGNORE INTO player_external_ids (
                player_id,
                external_id,
                source
            )
            SELECT
                player_id,
                external_id,
                'legacy'
            FROM players
            WHERE
                external_id IS NOT NULL
                AND external_id != ''
            """
        )

        self.connection.commit()

    @staticmethod
    def _normalize_name_for_match(
        value: str,
    ) -> str:
        return " ".join(
            value.strip().casefold().split()
        )

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