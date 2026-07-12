import random
from dataclasses import dataclass

from src.demo.names import FIRST_NAMES, LAST_NAMES


@dataclass(slots=True)
class DemoReferee:
    first_name: str
    last_name: str
    association: str


def generate_demo_referees(
    amount: int = 20,
    seed: int = 2027,
) -> list[DemoReferee]:
    random.seed(seed)

    referees = []
    used_names = set()

    while len(referees) < amount:
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        full_name = (first_name, last_name)

        if full_name in used_names:
            continue

        used_names.add(full_name)

        referees.append(
            DemoReferee(
                first_name=first_name,
                last_name=last_name,
                association="FVR",
            )
        )

    return referees