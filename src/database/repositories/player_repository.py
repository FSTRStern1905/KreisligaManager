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
        found_by_external_id = False

        if normalized_external_id:
            existing = (
                self.get_by_external_id(
                    normalized_external_id
                )
            )

            found_by_external_id = (
                existing is not None
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
            if (
                found_by_external_id
                and self._should_try_exact_identity_merge(
                    existing=existing,
                    incoming_first_name=normalized_first_name,
                    incoming_last_name=normalized_last_name,
                    team_id=team_id,
                    incoming_external_id=normalized_external_id,
                )
            ):
                merge_target = (
                    self._find_exact_identity_merge_target(
                        source_player_id=int(
                            existing["player_id"]
                        ),
                        team_id=team_id,
                        first_name=normalized_first_name,
                        last_name=normalized_last_name,
                    )
                )

                if merge_target is not None:
                    merged_player_id = self.merge_players(
                        source_player_id=int(
                            existing["player_id"]
                        ),
                        target_player_id=int(
                            merge_target["player_id"]
                        ),
                        commit=False,
                    )

                    existing = self.get(
                        merged_player_id
                    )

                    if existing is None:
                        raise RuntimeError(
                            "Zusammengeführter Spieler konnte "
                            "nicht erneut geladen werden."
                        )

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

            should_update_primary_id = (
                normalized_external_id
                and not existing["external_id"]
            )

            should_update_first_name = (
                normalized_first_name
                and (
                    not existing_first_name
                    or existing_is_placeholder
                )
                and not incoming_is_placeholder
            )

            should_update_last_name = (
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

    def _should_try_exact_identity_merge(
        self,
        existing: dict,
        incoming_first_name: str,
        incoming_last_name: str,
        team_id: int | None,
        incoming_external_id: str,
    ) -> bool:
        if team_id is None or team_id <= 0:
            return False

        normalized_first = (
            self._normalize_name_for_match(
                incoming_first_name
            )
        )
        normalized_last = (
            self._normalize_name_for_match(
                incoming_last_name
            )
        )

        if not normalized_first or not normalized_last:
            return False

        if self._is_unknown_placeholder(
            incoming_last_name,
            incoming_external_id,
        ):
            return False

        existing_first = (
            self._normalize_name_for_match(
                existing["first_name"] or ""
            )
        )
        existing_last = (
            self._normalize_name_for_match(
                existing["last_name"] or ""
            )
        )

        if (
            existing_first == normalized_first
            and existing_last == normalized_last
        ):
            return False

        existing_is_low_quality = (
            not existing_first
            or not existing_last
            or existing_first == existing_last
            or self._is_unknown_placeholder(
                existing["last_name"] or "",
                existing["external_id"] or "",
            )
        )

        if not existing_is_low_quality:
            return False

        existing_team_id = existing["team_id"]

        if (
            existing_team_id is not None
            and int(existing_team_id) != team_id
        ):
            return False

        return True

    def _find_exact_identity_merge_target(
        self,
        source_player_id: int,
        team_id: int | None,
        first_name: str,
        last_name: str,
    ) -> dict | None:
        if (
            source_player_id <= 0
            or team_id is None
            or team_id <= 0
        ):
            return None

        normalized_first = first_name.strip()
        normalized_last = last_name.strip()

        if not normalized_first or not normalized_last:
            return None

        rows = self.cursor.execute(
            f"""
            SELECT {self.COLUMNS}
            FROM players
            WHERE
                player_id != ?
                AND team_id = ?
                AND first_name = ?
                    COLLATE NOCASE
                AND last_name = ?
                    COLLATE NOCASE
            ORDER BY player_id
            LIMIT 2
            """,
            (
                source_player_id,
                team_id,
                normalized_first,
                normalized_last,
            ),
        ).fetchall()

        if len(rows) != 1:
            return None

        return self._row_to_dict(
            rows[0]
        )

    def merge_players(
        self,
        source_player_id: int,
        target_player_id: int,
        commit: bool = True,
    ) -> int:
        """
        Führt zwei bereits als identisch bestätigte Spieler zusammen.

        Alle bekannten Fremdschlüssel auf den Quellspieler werden auf den
        Zielspieler umgehängt. External-ID-Aliase bleiben erhalten.
        Doppelte Lineup-/Stat-Zeilen werden vor dem Umhängen entfernt.

        Die Methode entscheidet NICHT selbst, ob zwei Spieler identisch sind.
        """
        if source_player_id <= 0 or target_player_id <= 0:
            raise ValueError("Ungültige Spieler-ID.")

        if source_player_id == target_player_id:
            return target_player_id

        source = self.get(source_player_id)
        target = self.get(target_player_id)

        if source is None:
            raise ValueError("Quellspieler wurde nicht gefunden.")

        if target is None:
            raise ValueError("Zielspieler wurde nicht gefunden.")

        source_team_id = source["team_id"]
        target_team_id = target["team_id"]

        if (
            source_team_id is not None
            and target_team_id is not None
            and source_team_id != target_team_id
        ):
            raise ValueError(
                "Spieler aus unterschiedlichen Mannschaften "
                "dürfen nicht automatisch zusammengeführt werden."
            )

        try:
            self.connection.execute("SAVEPOINT merge_players")

            source_aliases = {
                row[0]
                for row in self.connection.execute(
                    """
                    SELECT external_id
                    FROM player_external_ids
                    WHERE player_id = ?
                    """,
                    (source_player_id,),
                ).fetchall()
                if row[0]
            }

            if source["external_id"]:
                source_aliases.add(source["external_id"])

            # Lineups können bereits eine Zeile für den Zielspieler im
            # selben Spiel besitzen. Vor dem Löschen der Quellzeile werden
            # relevante Qualitätsmerkmale zusammengeführt. Besonders wichtig:
            # War eine der beiden Zeilen Starter, muss der gemergte Spieler
            # Starter bleiben.
            self._merge_lineup_rows_before_player_merge(
                source_player_id=source_player_id,
                target_player_id=target_player_id,
            )

            # Spieler-Spiel-Statistiken müssen vor dem Löschen einer
            # Dubletten-Zeile zusammengeführt werden. Dabei werden Starter-,
            # Wechsel- und weitere Statistikwerte erhalten, ohne doppelte
            # Events blind zu addieren.
            self._merge_player_match_stats_rows_before_player_merge(
                source_player_id=source_player_id,
                target_player_id=target_player_id,
            )

            # Alle übrigen Spielerreferenzen automatisch erfassen.
            # Neben player_id wird auch related_player_id berücksichtigt,
            # damit z. B. Wechselbeziehungen nicht auf eine gelöschte
            # Spieler-ID zeigen.
            ignored_tables = {
                "players",
                "player_external_ids",
                "lineups",
                "player_match_stats",
            }

            for (
                table_name,
                reference_columns,
            ) in self._tables_with_player_references():
                if table_name in ignored_tables:
                    continue

                for column_name in reference_columns:
                    self.connection.execute(
                        f'UPDATE "{table_name}" '
                        f'SET "{column_name}" = ? '
                        f'WHERE "{column_name}" = ?',
                        (
                            target_player_id,
                            source_player_id,
                        ),
                    )

            if self._table_exists("lineups"):
                self.connection.execute(
                    """
                    UPDATE lineups
                    SET player_id = ?
                    WHERE player_id = ?
                    """,
                    (
                        target_player_id,
                        source_player_id,
                    ),
                )

            if self._table_exists("player_match_stats"):
                self.connection.execute(
                    """
                    UPDATE player_match_stats
                    SET player_id = ?
                    WHERE player_id = ?
                    """,
                    (
                        target_player_id,
                        source_player_id,
                    ),
                )

            # Alte Alias-Zeilen des Quellspielers entfernen und anschließend
            # auf den Zielspieler übertragen.
            self.connection.execute(
                """
                DELETE FROM player_external_ids
                WHERE player_id = ?
                """,
                (source_player_id,),
            )

            for external_id in sorted(source_aliases):
                self._add_external_id_alias(
                    player_id=target_player_id,
                    external_id=external_id,
                    source="merge",
                    commit=False,
                )

            # Falls der Zielspieler noch keine primäre External-ID besitzt,
            # darf die primäre ID des Quellspielers übernommen werden.
            if (
                not (target["external_id"] or "").strip()
                and (source["external_id"] or "").strip()
            ):
                self.connection.execute(
                    """
                    UPDATE players
                    SET external_id = ?
                    WHERE player_id = ?
                    """,
                    (
                        source["external_id"].strip(),
                        target_player_id,
                    ),
                )

            self.connection.execute(
                """
                DELETE FROM players
                WHERE player_id = ?
                """,
                (source_player_id,),
            )

            self.connection.execute("RELEASE SAVEPOINT merge_players")

            if commit:
                self.connection.commit()

            return target_player_id

        except Exception:
            self.connection.execute(
                "ROLLBACK TO SAVEPOINT merge_players"
            )
            self.connection.execute(
                "RELEASE SAVEPOINT merge_players"
            )
            raise

    def _merge_lineup_rows_before_player_merge(
        self,
        source_player_id: int,
        target_player_id: int,
    ) -> None:
        if not self._table_exists("lineups"):
            return

        columns = {
            row[1]
            for row in self.connection.execute(
                'PRAGMA table_info("lineups")'
            ).fetchall()
        }

        if (
            "match_id" not in columns
            or "player_id" not in columns
        ):
            return

        has_is_starting = "is_starting" in columns
        has_shirt_number = "shirt_number" in columns
        has_position = "position" in columns

        source_rows = self.connection.execute(
            """
            SELECT *
            FROM lineups
            WHERE player_id = ?
            ORDER BY match_id
            """,
            (source_player_id,),
        ).fetchall()

        column_names = [
            row[1]
            for row in self.connection.execute(
                'PRAGMA table_info("lineups")'
            ).fetchall()
        ]

        for source_row in source_rows:
            source_data = dict(
                zip(column_names, source_row)
            )
            match_id = source_data["match_id"]

            target_row = self.connection.execute(
                """
                SELECT *
                FROM lineups
                WHERE
                    match_id = ?
                    AND player_id = ?
                LIMIT 1
                """,
                (
                    match_id,
                    target_player_id,
                ),
            ).fetchone()

            if target_row is None:
                continue

            target_data = dict(
                zip(column_names, target_row)
            )

            updates = []
            values = []

            if has_is_starting:
                merged_starting = max(
                    int(source_data.get("is_starting") or 0),
                    int(target_data.get("is_starting") or 0),
                )
                if merged_starting != int(
                    target_data.get("is_starting") or 0
                ):
                    updates.append("is_starting = ?")
                    values.append(merged_starting)

            if has_shirt_number:
                target_number = target_data.get(
                    "shirt_number"
                )
                source_number = source_data.get(
                    "shirt_number"
                )

                if (
                    target_number is None
                    and source_number is not None
                ):
                    updates.append("shirt_number = ?")
                    values.append(source_number)

            if has_position:
                target_position = str(
                    target_data.get("position") or ""
                ).strip()
                source_position = str(
                    source_data.get("position") or ""
                ).strip()

                if (
                    not target_position
                    and source_position
                ):
                    updates.append("position = ?")
                    values.append(source_position)

            if updates:
                values.extend(
                    (
                        match_id,
                        target_player_id,
                    )
                )

                self.connection.execute(
                    f"""
                    UPDATE lineups
                    SET {", ".join(updates)}
                    WHERE
                        match_id = ?
                        AND player_id = ?
                    """,
                    tuple(values),
                )

        self._deduplicate_before_player_merge(
            table_name="lineups",
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            key_columns=("match_id",),
        )

    def _merge_player_match_stats_rows_before_player_merge(
        self,
        source_player_id: int,
        target_player_id: int,
    ) -> None:
        if not self._table_exists("player_match_stats"):
            return

        pragma_rows = self.connection.execute(
            'PRAGMA table_info("player_match_stats")'
        ).fetchall()

        column_names = [
            row[1]
            for row in pragma_rows
        ]
        columns = set(column_names)

        if (
            "match_id" not in columns
            or "player_id" not in columns
        ):
            return

        source_rows = self.connection.execute(
            """
            SELECT *
            FROM player_match_stats
            WHERE player_id = ?
            ORDER BY match_id
            """,
            (source_player_id,),
        ).fetchall()

        boolean_or_columns = (
            "is_starting",
            "was_substituted_in",
            "was_substituted_out",
            "clean_sheet",
        )

        numeric_max_columns = (
            "minutes_played",
            "goals",
            "own_goals",
            "assists",
            "yellow_cards",
            "yellow_red_cards",
            "red_cards",
        )

        nullable_min_columns = (
            "minute_in",
        )

        nullable_max_columns = (
            "minute_out",
        )

        fill_if_missing_columns = (
            "shirt_number",
            "position",
        )

        for source_row in source_rows:
            source_data = dict(
                zip(column_names, source_row)
            )
            match_id = source_data["match_id"]

            target_row = self.connection.execute(
                """
                SELECT *
                FROM player_match_stats
                WHERE
                    match_id = ?
                    AND player_id = ?
                LIMIT 1
                """,
                (
                    match_id,
                    target_player_id,
                ),
            ).fetchone()

            if target_row is None:
                continue

            target_data = dict(
                zip(column_names, target_row)
            )

            updates: list[str] = []
            values: list[object] = []

            for column_name in boolean_or_columns:
                if column_name not in columns:
                    continue

                merged_value = max(
                    int(
                        source_data.get(column_name)
                        or 0
                    ),
                    int(
                        target_data.get(column_name)
                        or 0
                    ),
                )

                current_value = int(
                    target_data.get(column_name)
                    or 0
                )

                if merged_value != current_value:
                    updates.append(
                        f'"{column_name}" = ?'
                    )
                    values.append(merged_value)

            for column_name in numeric_max_columns:
                if column_name not in columns:
                    continue

                source_value = int(
                    source_data.get(column_name)
                    or 0
                )
                target_value = int(
                    target_data.get(column_name)
                    or 0
                )

                merged_value = max(
                    source_value,
                    target_value,
                )

                if merged_value != target_value:
                    updates.append(
                        f'"{column_name}" = ?'
                    )
                    values.append(merged_value)

            for column_name in nullable_min_columns:
                if column_name not in columns:
                    continue

                source_value = source_data.get(
                    column_name
                )
                target_value = target_data.get(
                    column_name
                )

                available = [
                    int(value)
                    for value in (
                        source_value,
                        target_value,
                    )
                    if value is not None
                ]

                merged_value = (
                    min(available)
                    if available
                    else None
                )

                if merged_value != target_value:
                    updates.append(
                        f'"{column_name}" = ?'
                    )
                    values.append(merged_value)

            for column_name in nullable_max_columns:
                if column_name not in columns:
                    continue

                source_value = source_data.get(
                    column_name
                )
                target_value = target_data.get(
                    column_name
                )

                available = [
                    int(value)
                    for value in (
                        source_value,
                        target_value,
                    )
                    if value is not None
                ]

                merged_value = (
                    max(available)
                    if available
                    else None
                )

                if merged_value != target_value:
                    updates.append(
                        f'"{column_name}" = ?'
                    )
                    values.append(merged_value)

            for column_name in fill_if_missing_columns:
                if column_name not in columns:
                    continue

                source_value = source_data.get(
                    column_name
                )
                target_value = target_data.get(
                    column_name
                )

                target_missing = (
                    target_value is None
                    or (
                        isinstance(target_value, str)
                        and not target_value.strip()
                    )
                )

                source_available = (
                    source_value is not None
                    and (
                        not isinstance(
                            source_value,
                            str,
                        )
                        or bool(
                            source_value.strip()
                        )
                    )
                )

                if target_missing and source_available:
                    updates.append(
                        f'"{column_name}" = ?'
                    )
                    values.append(source_value)

            if updates:
                values.extend(
                    (
                        match_id,
                        target_player_id,
                    )
                )

                self.connection.execute(
                    f"""
                    UPDATE player_match_stats
                    SET {", ".join(updates)}
                    WHERE
                        match_id = ?
                        AND player_id = ?
                    """,
                    tuple(values),
                )

        self._deduplicate_before_player_merge(
            table_name="player_match_stats",
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            key_columns=("match_id",),
        )

    def _deduplicate_before_player_merge(
        self,
        table_name: str,
        source_player_id: int,
        target_player_id: int,
        key_columns: tuple[str, ...],
    ) -> None:
        if not self._table_exists(table_name):
            return

        columns = {
            row[1]
            for row in self.connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
        }

        if "player_id" not in columns:
            return

        usable_keys = [
            column
            for column in key_columns
            if column in columns
        ]

        if not usable_keys:
            return

        conditions = " AND ".join(
            f'target."{column}" = source."{column}"'
            for column in usable_keys
        )

        self.connection.execute(
            f"""
            DELETE FROM "{table_name}" AS source
            WHERE source.player_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM "{table_name}" AS target
                  WHERE target.player_id = ?
                    AND {conditions}
              )
            """,
            (
                source_player_id,
                target_player_id,
            ),
        )

    def _tables_with_player_references(
        self,
    ) -> list[tuple[str, tuple[str, ...]]]:
        tables: list[
            tuple[str, tuple[str, ...]]
        ] = []

        rows = self.connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for row in rows:
            table_name = row[0]

            columns = {
                column[1]
                for column in self.connection.execute(
                    f'PRAGMA table_info("{table_name}")'
                ).fetchall()
            }

            reference_columns = tuple(
                column_name
                for column_name in (
                    "player_id",
                    "related_player_id",
                )
                if column_name in columns
            )

            if reference_columns:
                tables.append(
                    (
                        table_name,
                        reference_columns,
                    )
                )

        return tables

    def _table_exists(
        self,
        table_name: str,
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            LIMIT 1
            """,
            (table_name,),
        ).fetchone()

        return row is not None

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