from src.database.repositories.base_repository import BaseRepository


class ClubRepository(BaseRepository):

    TABLE = "clubs"
    ID = "club_id"

    def get_all(self) -> list[dict]:
        return self.fetch_all(
            self.TABLE,
            order_by="name ASC",
        )

    def get(
        self,
        club_id: int,
    ) -> dict | None:
        return self.fetch_by_id(
            self.TABLE,
            self.ID,
            club_id,
        )

    def get_by_name(
        self,
        name: str,
    ) -> dict | None:
        normalized_name = name.strip()

        if not normalized_name:
            return None

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM clubs
            WHERE name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (normalized_name,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def add(
        self,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id: int | None = None,
    ) -> int:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Der Vereinsname darf nicht leer sein."
            )

        return self.insert(
            self.TABLE,
            {
                "name": normalized_name,
                "short_name": short_name.strip(),
                "city": city.strip(),
                "association_id": association_id,
            },
        )

    def get_or_create(
        self,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id: int | None = None,
    ) -> int:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Der Vereinsname darf nicht leer sein."
            )

        existing_club = self.get_by_name(
            normalized_name
        )

        if existing_club is not None:
            return int(
                existing_club[self.ID]
            )

        club_id = self.add(
            name=normalized_name,
            short_name=short_name,
            city=city,
            association_id=association_id,
        )

        self.connection.commit()

        return club_id

    def update(
        self,
        club_id: int,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id: int | None = None,
    ) -> int:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Der Vereinsname darf nicht leer sein."
            )

        return super().update(
            self.TABLE,
            self.ID,
            club_id,
            {
                "name": normalized_name,
                "short_name": short_name.strip(),
                "city": city.strip(),
                "association_id": association_id,
            },
        )

    def delete(
        self,
        club_id: int,
    ) -> int:
        return super().delete(
            self.TABLE,
            self.ID,
            club_id,
        )

    def search(
        self,
        text: str,
    ) -> list[dict]:
        search_text = text.strip()

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM clubs
            WHERE
                name LIKE ?
                OR short_name LIKE ?
                OR city LIKE ?
            ORDER BY name ASC
            """,
            (
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
            ),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]