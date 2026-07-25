from dataclasses import dataclass


@dataclass(slots=True)
class Association:
    association_id: int | None = None
    name: str = ""
    country: str = "Deutschland"
    short_name: str = ""
    active: bool = True