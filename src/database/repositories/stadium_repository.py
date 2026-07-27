import sqlite3


class StadiumRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self._ensure_indexes()

    def get(
        self,
        stadium_id: int,
    ) -> dict | None:
        if stadium_id <= 0:
            raise ValueError(
                "Ungültige Spielstätten-ID."
            )

        self.cursor.execute(
            """
            SELECT
                stadium_id,
                name,
                city,
                capacity
            FROM stadiums
            WHERE stadium_id = ?
            LIMIT 1
            """,
            (stadium_id,),
        )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def get_all(
        self,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                stadium_id,
                name,
                city,
                capacity
            FROM stadiums
            ORDER BY
                city COLLATE NOCASE,
                name COLLATE NOCASE
            """
        )

        return [
            self._row_to_dict(row)
            for row in self.cursor.fetchall()
        ]

    def get_by_name(
        self,
        name: str,
        city: str = "",
    ) -> dict | None:
        normalized_name = " ".join(
            name.split()
        )

        normalized_city = " ".join(
            city.split()
        )

        if not normalized_name:
            return None

        if normalized_city:
            self.cursor.execute(
                """
                SELECT
                    stadium_id,
                    name,
                    city,
                    capacity
                FROM stadiums
                WHERE
                    name = ? COLLATE NOCASE
                    AND city = ? COLLATE NOCASE
                LIMIT 1
                """,
                (
                    normalized_name,
                    normalized_city,
                ),
            )
        else:
            self.cursor.execute(
                """
                SELECT
                    stadium_id,
                    name,
                    city,
                    capacity
                FROM stadiums
                WHERE name = ? COLLATE NOCASE
                ORDER BY stadium_id
                LIMIT 1
                """,
                (normalized_name,),
            )

        return self._row_to_dict(
            self.cursor.fetchone()
        )

    def search(
        self,
        search_text: str,
    ) -> list[dict]:
        normalized_search = " ".join(
            search_text.split()
        )

        if not normalized_search:
            return []

        search_value = (
            f"%{normalized_search}%"
        )

        self.cursor.execute(
            """
            SELECT
                stadium_id,
                name,
                city,
                capacity
            FROM stadiums
            WHERE
                name LIKE ? COLLATE NOCASE
                OR city LIKE ? COLLATE NOCASE
            ORDER BY
                city COLLATE NOCASE,
                name COLLATE NOCASE
            """,
            (
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
        name: str,
        city: str = "",
        capacity: int | None = None,
        commit: bool = True,
    ) -> int:
        normalized_name = " ".join(
            name.split()
        )

        normalized_city = " ".join(
            city.split()
        )

        self._validate(
            name=normalized_name,
            capacity=capacity,
        )

        self.cursor.execute(
            """
            INSERT INTO stadiums (
                name,
                city,
                capacity
            )
            VALUES (?, ?, ?)
            """,
            (
                normalized_name,
                normalized_city,
                capacity,
            ),
        )

        if commit:
            self.connection.commit()

        return int(
            self.cursor.lastrowid
        )

    def update(
        self,
        stadium_id: int,
        name: str,
        city: str = "",
        capacity: int | None = None,
        commit: bool = True,
    ) -> None:
        if stadium_id <= 0:
            raise ValueError(
                "Ungültige Spielstätten-ID."
            )

        normalized_name = " ".join(
            name.split()
        )

        normalized_city = " ".join(
            city.split()
        )

        self._validate(
            name=normalized_name,
            capacity=capacity,
        )

        self.cursor.execute(
            """
            UPDATE stadiums
            SET
                name = ?,
                city = ?,
                capacity = ?
            WHERE stadium_id = ?
            """,
            (
                normalized_name,
                normalized_city,
                capacity,
                stadium_id,
            ),
        )

        if self.cursor.rowcount == 0:
            raise ValueError(
                "Spielstätte wurde nicht gefunden."
            )

        if commit:
            self.connection.commit()

    def get_or_create(
        self,
        name: str,
        city: str = "",
        capacity: int | None = None,
        commit: bool = True,
    ) -> int:
        normalized_name = " ".join(
            name.split()
        )

        normalized_city = " ".join(
            city.split()
        )

        if not normalized_name:
            raise ValueError(
                "Der Name der Spielstätte darf "
                "nicht leer sein."
            )

        existing = self.get_by_name(
            name=normalized_name,
            city=normalized_city,
        )

        if existing is not None:
            stadium_id = int(
                existing["stadium_id"]
            )

            existing_capacity = (
                existing["capacity"]
            )

            if (
                capacity is not None
                and existing_capacity is None
            ):
                self.update(
                    stadium_id=stadium_id,
                    name=existing["name"],
                    city=(
                        normalized_city
                        or existing["city"]
                    ),
                    capacity=capacity,
                    commit=commit,
                )

            return stadium_id

        return self.add(
            name=normalized_name,
            city=normalized_city,
            capacity=capacity,
            commit=commit,
        )

    def upsert(
        self,
        name: str,
        city: str = "",
        capacity: int | None = None,
        commit: bool = True,
    ) -> tuple[int, bool]:
        normalized_name = " ".join(
            name.split()
        )

        normalized_city = " ".join(
            city.split()
        )

        existing = self.get_by_name(
            name=normalized_name,
            city=normalized_city,
        )

        if existing is None:
            stadium_id = self.add(
                name=normalized_name,
                city=normalized_city,
                capacity=capacity,
                commit=commit,
            )

            return stadium_id, True

        stadium_id = int(
            existing["stadium_id"]
        )

        self.update(
            stadium_id=stadium_id,
            name=normalized_name,
            city=(
                normalized_city
                or existing["city"]
            ),
            capacity=(
                capacity
                if capacity is not None
                else existing["capacity"]
            ),
            commit=commit,
        )

        return stadium_id, False

    def delete(
        self,
        stadium_id: int,
        commit: bool = True,
    ) -> int:
        if stadium_id <= 0:
            raise ValueError(
                "Ungültige Spielstätten-ID."
            )

        self.cursor.execute(
            """
            DELETE FROM stadiums
            WHERE stadium_id = ?
            """,
            (stadium_id,),
        )

        deleted = self.cursor.rowcount

        if commit:
            self.connection.commit()

        return deleted

    def count_matches(
        self,
        stadium_id: int,
    ) -> int:
        if stadium_id <= 0:
            raise ValueError(
                "Ungültige Spielstätten-ID."
            )

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE stadium_id = ?
            """,
            (stadium_id,),
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
                idx_stadiums_unique_name_city
            ON stadiums(
                name COLLATE NOCASE,
                city COLLATE NOCASE
            )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_stadiums_city
            ON stadiums(
                city COLLATE NOCASE
            )
            """
        )

        self.connection.commit()

    @staticmethod
    def _validate(
        name: str,
        capacity: int | None,
    ) -> None:
        if not name:
            raise ValueError(
                "Der Name der Spielstätte darf "
                "nicht leer sein."
            )

        if (
            capacity is not None
            and capacity < 0
        ):
            raise ValueError(
                "Die Kapazität darf nicht "
                "negativ sein."
            )

    @staticmethod
    def _row_to_dict(
        row: sqlite3.Row | tuple | None,
    ) -> dict | None:
        if row is None:
            return None

        return {
            "stadium_id": row[0],
            "name": row[1],
            "city": row[2] or "",
            "capacity": row[3],
        }