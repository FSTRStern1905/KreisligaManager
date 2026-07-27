import sqlite3


class LineupRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self._ensure_indexes()

    def get(
        self,
        lineup_id: int,
    ) -> dict | None:
        if lineup_id <= 0:
            raise ValueError(
                "Ungültige Aufstellungs-ID."
            )

        self.cursor.execute(
            """
            SELECT
                lineup_id,
                match_id,
                team_id,
                player_id,
                is_starting,
                shirt_number,
                position
            FROM lineups
            WHERE lineup_id = ?
            LIMIT 1
            """,
            (lineup_id,),
        )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

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
                lineups.lineup_id,
                lineups.match_id,
                lineups.team_id,
                lineups.player_id,
                lineups.is_starting,
                lineups.shirt_number,
                lineups.position
            FROM lineups
            INNER JOIN players
                ON players.player_id =
                    lineups.player_id
            WHERE lineups.match_id = ?
            ORDER BY
                lineups.team_id,
                lineups.is_starting DESC,
                lineups.shirt_number,
                players.last_name COLLATE NOCASE,
                players.first_name COLLATE NOCASE
            """,
            (match_id,),
        )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_match_and_team(
        self,
        match_id: int,
        team_id: int,
    ) -> list[dict]:
        self._validate_ids(
            match_id=match_id,
            team_id=team_id,
            player_id=1,
        )

        self.cursor.execute(
            """
            SELECT
                lineups.lineup_id,
                lineups.match_id,
                lineups.team_id,
                lineups.player_id,
                lineups.is_starting,
                lineups.shirt_number,
                lineups.position
            FROM lineups
            INNER JOIN players
                ON players.player_id =
                    lineups.player_id
            WHERE
                lineups.match_id = ?
                AND lineups.team_id = ?
            ORDER BY
                lineups.is_starting DESC,
                lineups.shirt_number,
                players.last_name COLLATE NOCASE,
                players.first_name COLLATE NOCASE
            """,
            (
                match_id,
                team_id,
            ),
        )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def get_player_lineups(
        self,
        player_id: int,
    ) -> list[dict]:
        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

        self.cursor.execute(
            """
            SELECT
                lineup_id,
                match_id,
                team_id,
                player_id,
                is_starting,
                shirt_number,
                position
            FROM lineups
            WHERE player_id = ?
            ORDER BY match_id DESC
            """,
            (player_id,),
        )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def get_player(
        self,
        match_id: int,
        team_id: int,
        player_id: int,
    ) -> dict | None:
        self._validate_ids(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
        )

        self.cursor.execute(
            """
            SELECT
                lineup_id,
                match_id,
                team_id,
                player_id,
                is_starting,
                shirt_number,
                position
            FROM lineups
            WHERE
                match_id = ?
                AND team_id = ?
                AND player_id = ?
            LIMIT 1
            """,
            (
                match_id,
                team_id,
                player_id,
            ),
        )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def add(
        self,
        match_id: int,
        team_id: int,
        player_id: int,
        is_starting: bool = False,
        shirt_number: int | None = None,
        position: str = "",
        commit: bool = True,
    ) -> int:
        self._validate(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
            shirt_number=shirt_number,
        )

        self.cursor.execute(
            """
            INSERT INTO lineups (
                match_id,
                team_id,
                player_id,
                is_starting,
                shirt_number,
                position
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                match_id,
                team_id,
                player_id,
                int(is_starting),
                shirt_number,
                position.strip(),
            ),
        )

        if commit:
            self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def update(
        self,
        lineup_id: int,
        match_id: int,
        team_id: int,
        player_id: int,
        is_starting: bool = False,
        shirt_number: int | None = None,
        position: str = "",
        commit: bool = True,
    ) -> None:
        if lineup_id <= 0:
            raise ValueError(
                "Ungültige Aufstellungs-ID."
            )

        self._validate(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
            shirt_number=shirt_number,
        )

        self.cursor.execute(
            """
            UPDATE lineups
            SET
                match_id = ?,
                team_id = ?,
                player_id = ?,
                is_starting = ?,
                shirt_number = ?,
                position = ?
            WHERE lineup_id = ?
            """,
            (
                match_id,
                team_id,
                player_id,
                int(is_starting),
                shirt_number,
                position.strip(),
                lineup_id,
            ),
        )

        if self.cursor.rowcount == 0:
            raise ValueError(
                "Aufstellungseintrag wurde "
                "nicht gefunden."
            )

        if commit:
            self.connection.commit()

    def upsert(
        self,
        match_id: int,
        team_id: int,
        player_id: int,
        is_starting: bool = False,
        shirt_number: int | None = None,
        position: str = "",
        commit: bool = True,
    ) -> tuple[int, bool]:
        existing = self.get_player(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
        )

        if existing is None:
            lineup_id = self.add(
                match_id=match_id,
                team_id=team_id,
                player_id=player_id,
                is_starting=is_starting,
                shirt_number=shirt_number,
                position=position,
                commit=commit,
            )

            return lineup_id, True

        lineup_id = int(
            existing["lineup_id"]
        )

        self.update(
            lineup_id=lineup_id,
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
            is_starting=is_starting,
            shirt_number=shirt_number,
            position=position,
            commit=commit,
        )

        return lineup_id, False

    def replace_match_lineups(
        self,
        match_id: int,
        lineups: list[dict],
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

            inserted = 0

            for lineup in lineups:
                self.add(
                    match_id=match_id,
                    team_id=int(
                        lineup["team_id"]
                    ),
                    player_id=int(
                        lineup["player_id"]
                    ),
                    is_starting=bool(
                        lineup.get(
                            "is_starting",
                            False,
                        )
                    ),
                    shirt_number=lineup.get(
                        "shirt_number"
                    ),
                    position=str(
                        lineup.get(
                            "position",
                            "",
                        )
                    ),
                    commit=False,
                )

                inserted += 1

            self.connection.commit()

            return inserted

        except Exception:
            self.connection.rollback()
            raise

    def delete(
        self,
        lineup_id: int,
        commit: bool = True,
    ) -> int:
        if lineup_id <= 0:
            raise ValueError(
                "Ungültige Aufstellungs-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM lineups
            WHERE lineup_id = ?
            """,
            (lineup_id,),
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
            DELETE FROM lineups
            WHERE match_id = ?
            """,
            (match_id,),
        )

        deleted = self.cursor.rowcount

        if commit:
            self.connection.commit()

        return deleted

    def delete_by_match_and_team(
        self,
        match_id: int,
        team_id: int,
        commit: bool = True,
    ) -> int:
        self._validate_ids(
            match_id=match_id,
            team_id=team_id,
            player_id=1,
        )

        self.cursor.execute(
            """
            DELETE FROM lineups
            WHERE
                match_id = ?
                AND team_id = ?
            """,
            (
                match_id,
                team_id,
            ),
        )

        deleted = self.cursor.rowcount

        if commit:
            self.connection.commit()

        return deleted

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
            FROM lineups
            WHERE match_id = ?
            """,
            (match_id,),
        )

        return int(
            self.cursor.fetchone()[0]
        )

    def count_starters(
        self,
        match_id: int,
        team_id: int,
    ) -> int:
        self._validate_ids(
            match_id=match_id,
            team_id=team_id,
            player_id=1,
        )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM lineups
            WHERE
                match_id = ?
                AND team_id = ?
                AND is_starting = 1
            """,
            (
                match_id,
                team_id,
            ),
        )

        return int(
            self.cursor.fetchone()[0]
        )

    def _ensure_indexes(
        self,
    ) -> None:
        self.cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_lineups_unique_player
            ON lineups(
                match_id,
                team_id,
                player_id
            )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_lineups_match_team
            ON lineups(
                match_id,
                team_id
            )
            """
        )

        self.connection.commit()

    def _validate(
        self,
        match_id: int,
        team_id: int,
        player_id: int,
        shirt_number: int | None,
    ) -> None:
        self._validate_ids(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
        )

        if (
            shirt_number is not None
            and shirt_number < 0
        ):
            raise ValueError(
                "Die Rückennummer darf nicht "
                "negativ sein."
            )

    @staticmethod
    def _validate_ids(
        match_id: int,
        team_id: int,
        player_id: int,
    ) -> None:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        if player_id <= 0:
            raise ValueError(
                "Ungültige Spieler-ID."
            )

    @staticmethod
    def _row_to_dict(
        row: sqlite3.Row | tuple | None,
    ) -> dict | None:
        if row is None:
            return None

        return {
            "lineup_id": row[0],
            "match_id": row[1],
            "team_id": row[2],
            "player_id": row[3],
            "is_starting": bool(row[4]),
            "shirt_number": row[5],
            "position": row[6] or "",
        }