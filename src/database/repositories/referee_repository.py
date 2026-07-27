import sqlite3


class RefereeRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self._ensure_indexes()

    def get(
        self,
        referee_id: int,
    ) -> dict | None:
        if referee_id <= 0:
            raise ValueError(
                "Ungültige Schiedsrichter-ID."
            )

        self.cursor.execute(
            """
            SELECT
                referee_id,
                first_name,
                last_name,
                association
            FROM referees
            WHERE referee_id = ?
            LIMIT 1
            """,
            (referee_id,),
        )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def get_all(self) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                referee_id,
                first_name,
                last_name,
                association
            FROM referees
            ORDER BY
                last_name COLLATE NOCASE,
                first_name COLLATE NOCASE
            """
        )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_name(
        self,
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

        self.cursor.execute(
            """
            SELECT
                referee_id,
                first_name,
                last_name,
                association
            FROM referees
            WHERE
                first_name = ?
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

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def get_by_full_name(
        self,
        full_name: str,
    ) -> dict | None:
        first_name, last_name = (
            self.split_name(full_name)
        )

        if not last_name:
            return None

        return self.get_by_name(
            first_name=first_name,
            last_name=last_name,
        )

    def search(
        self,
        search_text: str,
    ) -> list[dict]:
        normalized_search = (
            search_text.strip()
        )

        if not normalized_search:
            return []

        search_value = (
            f"%{normalized_search}%"
        )

        self.cursor.execute(
            """
            SELECT
                referee_id,
                first_name,
                last_name,
                association
            FROM referees
            WHERE
                first_name LIKE ?
                    COLLATE NOCASE
                OR last_name LIKE ?
                    COLLATE NOCASE
                OR (
                    TRIM(
                        COALESCE(first_name, '')
                        || ' '
                        || COALESCE(last_name, '')
                    )
                ) LIKE ? COLLATE NOCASE
                OR association LIKE ?
                    COLLATE NOCASE
            ORDER BY
                last_name COLLATE NOCASE,
                first_name COLLATE NOCASE
            """,
            (
                search_value,
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
        association: str = "",
        commit: bool = True,
    ) -> int:
        normalized_first_name = (
            first_name.strip()
        )
        normalized_last_name = (
            last_name.strip()
        )
        normalized_association = (
            association.strip()
        )

        if not normalized_last_name:
            raise ValueError(
                "Der Nachname darf nicht leer sein."
            )

        self.cursor.execute(
            """
            INSERT INTO referees (
                first_name,
                last_name,
                association
            )
            VALUES (?, ?, ?)
            """,
            (
                normalized_first_name,
                normalized_last_name,
                normalized_association,
            ),
        )

        if commit:
            self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def update(
        self,
        referee_id: int,
        first_name: str,
        last_name: str,
        association: str = "",
        commit: bool = True,
    ) -> None:
        if referee_id <= 0:
            raise ValueError(
                "Ungültige Schiedsrichter-ID."
            )

        normalized_first_name = (
            first_name.strip()
        )
        normalized_last_name = (
            last_name.strip()
        )
        normalized_association = (
            association.strip()
        )

        if not normalized_last_name:
            raise ValueError(
                "Der Nachname darf nicht leer sein."
            )

        self.cursor.execute(
            """
            UPDATE referees
            SET
                first_name = ?,
                last_name = ?,
                association = ?
            WHERE referee_id = ?
            """,
            (
                normalized_first_name,
                normalized_last_name,
                normalized_association,
                referee_id,
            ),
        )

        if self.cursor.rowcount == 0:
            raise ValueError(
                "Schiedsrichter wurde nicht gefunden."
            )

        if commit:
            self.connection.commit()

    def get_or_create(
        self,
        first_name: str,
        last_name: str,
        association: str = "",
        commit: bool = True,
    ) -> int:
        existing = self.get_by_name(
            first_name=first_name,
            last_name=last_name,
        )

        if existing is not None:
            referee_id = int(
                existing["referee_id"]
            )

            normalized_association = (
                association.strip()
            )

            if (
                normalized_association
                and not existing["association"]
            ):
                self.update(
                    referee_id=referee_id,
                    first_name=(
                        existing["first_name"]
                    ),
                    last_name=(
                        existing["last_name"]
                    ),
                    association=normalized_association,
                    commit=commit,
                )

            return referee_id

        return self.add(
            first_name=first_name,
            last_name=last_name,
            association=association,
            commit=commit,
        )

    def get_or_create_by_full_name(
        self,
        full_name: str,
        association: str = "",
        commit: bool = True,
    ) -> int | None:
        first_name, last_name = (
            self.split_name(full_name)
        )

        if not last_name:
            return None

        return self.get_or_create(
            first_name=first_name,
            last_name=last_name,
            association=association,
            commit=commit,
        )

    def upsert(
        self,
        first_name: str,
        last_name: str,
        association: str = "",
        commit: bool = True,
    ) -> tuple[int, bool]:
        existing = self.get_by_name(
            first_name=first_name,
            last_name=last_name,
        )

        if existing is None:
            referee_id = self.add(
                first_name=first_name,
                last_name=last_name,
                association=association,
                commit=commit,
            )

            return referee_id, True

        referee_id = int(
            existing["referee_id"]
        )

        self.update(
            referee_id=referee_id,
            first_name=first_name,
            last_name=last_name,
            association=(
                association
                or existing["association"]
            ),
            commit=commit,
        )

        return referee_id, False

    def delete(
        self,
        referee_id: int,
        commit: bool = True,
    ) -> int:
        if referee_id <= 0:
            raise ValueError(
                "Ungültige Schiedsrichter-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM referees
            WHERE referee_id = ?
            """,
            (referee_id,),
        )

        deleted = self.cursor.rowcount

        if commit:
            self.connection.commit()

        return deleted

    def count_matches(
        self,
        referee_id: int,
    ) -> int:
        if referee_id <= 0:
            raise ValueError(
                "Ungültige Schiedsrichter-ID."
            )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE referee_id = ?
            """,
            (referee_id,),
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
                idx_referees_unique_name
            ON referees(
                first_name COLLATE NOCASE,
                last_name COLLATE NOCASE
            )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_referees_last_name
            ON referees(
                last_name COLLATE NOCASE
            )
            """
        )

        self.connection.commit()

    @staticmethod
    def split_name(
        full_name: str,
    ) -> tuple[str, str]:
        normalized_name = " ".join(
            full_name.split()
        )

        if not normalized_name:
            return "", ""

        parts = normalized_name.split(" ")

        if len(parts) == 1:
            return "", parts[0]

        first_name = " ".join(
            parts[:-1]
        )

        last_name = parts[-1]

        return first_name, last_name

    @staticmethod
    def _row_to_dict(
        row: sqlite3.Row | tuple | None,
    ) -> dict | None:
        if row is None:
            return None

        return {
            "referee_id": row[0],
            "first_name": row[1] or "",
            "last_name": row[2],
            "association": row[3] or "",
        }