import random
from dataclasses import dataclass

from src.demo.clubs import DEMO_CLUBS


@dataclass(slots=True)
class DemoStadium:
    club_name: str
    name: str
    city: str
    capacity: int


STADIUM_NAMES = [
    "Waldstadion",
    "Sportpark",
    "Moselstadion",
    "Rheinstadion",
    "Eichenstadion",
    "Sonnenhof-Arena",
    "Bergstadion",
    "Lindenpark",
    "Adlerstadion",
    "Rotbach-Arena",
    "Blaufels-Stadion",
    "Sportanlage am Rhein",
]


def generate_demo_stadiums(
    seed: int = 2026,
) -> list[DemoStadium]:
    random.seed(seed)

    stadiums = []

    for index, club in enumerate(DEMO_CLUBS):
        stadium_name = STADIUM_NAMES[
            index % len(STADIUM_NAMES)
        ]

        capacity = random.randint(800, 6500)

        stadiums.append(
            DemoStadium(
                club_name=club.name,
                name=stadium_name,
                city=club.city,
                capacity=capacity,
            )
        )

    return stadiums