from src.database.repositories.base_repository import BaseRepository


class ClubRepository(BaseRepository):

    TABLE = "clubs"
    ID = "club_id"

    def get_all(self) -> list[dict]:
        return self.fetch_all(
            self.TABLE,
            order_by="name ASC"
        )

    def get(self, club_id: int) -> dict | None:
        return self.fetch_by_id(
            self.TABLE,
            self.ID,
            club_id
        )

    def add(
        self,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id: int | None = None
    ) -> int:

        return self.insert(
            self.TABLE,
            {
                "name": name,
                "short_name": short_name,
                "city": city,
                "association_id": association_id
            }
        )

    def update_club(
        self,
        club_id: int,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id: int | None = None
    ) -> int:

        return self.update(
            self.TABLE,
            self.ID,
            club_id,
            {
                "name": name,
                "short_name": short_name,
                "city": city,
                "association_id": association_id
            }
        )

    def delete_club(self, club_id: int):

        return self.delete(
            self.TABLE,
            self.ID,
            club_id
        )

    def search(self, text: str):

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *

            FROM clubs

            WHERE
                name LIKE ?
                OR short_name LIKE ?
                OR city LIKE ?

            ORDER BY name
            """,
            (
                f"%{text}%",
                f"%{text}%",
                f"%{text}%"
            )
        )

        return [dict(row) for row in cursor.fetchall()]