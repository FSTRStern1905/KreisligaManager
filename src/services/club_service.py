from src.database.repositories.club_repository import ClubRepository


class ClubService:

    def __init__(self, connection):
        self.repository = ClubRepository(connection)

    def get_all(self):
        return self.repository.get_all()

    def get(self, club_id: int):
        return self.repository.get(club_id)

    def search(self, text: str):

        text = text.strip()

        if text == "":
            return self.get_all()

        return self.repository.search(text)

    def create(
        self,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id=None
    ) -> int:

        name = name.strip()
        short_name = short_name.strip()
        city = city.strip()

        if name == "":
            raise ValueError("Bitte einen Vereinsnamen eingeben.")

        clubs = self.get_all()

        for club in clubs:

            if club["name"].lower() == name.lower():

                raise ValueError(
                    "Der Verein existiert bereits."
                )

        return self.repository.add(
            name=name,
            short_name=short_name,
            city=city,
            association_id=association_id
        )

    def update(
        self,
        club_id: int,
        name: str,
        short_name: str = "",
        city: str = "",
        association_id=None
    ):

        name = name.strip()

        if name == "":
            raise ValueError("Bitte einen Vereinsnamen eingeben.")

        return self.repository.update_club(
            club_id,
            name,
            short_name,
            city,
            association_id
        )

    def delete(self, club_id: int):

        return self.repository.delete_club(club_id)