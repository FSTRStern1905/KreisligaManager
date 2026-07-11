import random
from dataclasses import dataclass
from datetime import date

from src.demo.names import FIRST_NAMES, LAST_NAMES, POSITIONS, FEET


@dataclass(slots=True)
class DemoPlayer:
    first_name: str
    last_name: str
    position: str
    number: int
    foot: str
    birthdate: str
    strength: int


def generate_players_for_club(club_strength: int, seed: int) -> list[DemoPlayer]:
    random.seed(seed)

    players = []
    used_numbers = set()

    squad_template = [
        ("Torwart", 2),
        ("Innenverteidiger", 4),
        ("Außenverteidiger", 4),
        ("Defensives Mittelfeld", 3),
        ("Zentrales Mittelfeld", 3),
        ("Offensives Mittelfeld", 2),
        ("Flügel", 2),
        ("Stürmer", 2),
    ]

    for position, amount in squad_template:
        for _ in range(amount):
            number = _generate_number(used_numbers)
            used_numbers.add(number)

            strength = max(35, min(99, club_strength + random.randint(-15, 15)))

            player = DemoPlayer(
                first_name=random.choice(FIRST_NAMES),
                last_name=random.choice(LAST_NAMES),
                position=position,
                number=number,
                foot=random.choice(FEET),
                birthdate=_generate_birthdate(),
                strength=strength,
            )

            players.append(player)

    return players


def _generate_number(used_numbers: set[int]) -> int:
    while True:
        number = random.randint(1, 30)
        if number not in used_numbers:
            return number


def _generate_birthdate() -> str:
    year = random.randint(1988, 2007)
    month = random.randint(1, 12)
    day = random.randint(1, 28)

    return date(year, month, day).isoformat()