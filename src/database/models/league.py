from dataclasses import dataclass


@dataclass(slots=True)
class League:
    """
    Datenmodell einer Liga.
    """

    league_id: int | None = None
    association_id: int | None = None
    name: str = ""
    level: int = 1
    season_type: str = "Liga"
    active: bool = True

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        if self.level > 0:
            return f"{self.name} (Level {self.level})"

        return self.name