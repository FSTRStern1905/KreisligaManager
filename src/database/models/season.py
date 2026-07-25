from dataclasses import dataclass


@dataclass(slots=True)
class Season:
    season_id: int | None = None
    name: str = ""
    start_date: str | None = None
    end_date: str | None = None
    external_id: str = ""
    active: bool = False

    @property
    def display_name(self) -> str:
        if self.start_date and self.end_date:
            return (
                f"{self.name} | "
                f"{self.start_date} bis {self.end_date}"
            )

        return self.name