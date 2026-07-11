from dataclasses import dataclass


@dataclass(slots=True)
class Club:
    """
    Datenmodell eines Vereins.
    """

    club_id: int | None = None

    association_id: int | None = None

    name: str = ""
    short_name: str = ""
    city: str = ""

    founded: int | None = None

    country: str = "Deutschland"

    logo: str = ""

    website: str = ""

    notes: str = ""

    active: bool = True

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        """
        Gibt den Kurznamen zurück,
        falls vorhanden.
        """

        if self.short_name.strip():
            return self.short_name

        return self.name

    def to_dict(self) -> dict:
        """
        Wandelt das Objekt in ein Dictionary um.
        """

        return {
            "club_id": self.club_id,
            "association_id": self.association_id,
            "name": self.name,
            "short_name": self.short_name,
            "city": self.city,
            "founded": self.founded,
            "country": self.country,
            "logo": self.logo,
            "website": self.website,
            "notes": self.notes,
            "active": self.active,
        }