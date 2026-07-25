from dataclasses import dataclass


@dataclass(slots=True)
class Association:
    association_id: int | None = None
    country_id: int | None = None
    name: str = ""
    short_name: str = ""
    country: str = "Deutschland"
