from dataclasses import dataclass


@dataclass(slots=True)
class Competition:
    """
    Datenmodell eines Wettbewerbs.

    Beispiele:
    - Kreisliga A 2026/27
    - Kreisliga B 2026/27
    - Kreispokal 2026/27
    """

    competition_id: int | None = None

    league_id: int | None = None

    season_id: int | None = None

    name: str = ""

    active: bool = True

    schedule_url: str = ""
    last_schedule_sync: str | None = None

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        return self.name