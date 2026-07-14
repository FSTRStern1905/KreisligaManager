import random
import sqlite3

from src.demo.clubs import DEMO_CLUBS
from src.demo.players import generate_players_for_club


class DemoPlayerGenerator:
    def __init__(
        self,
        connection: sqlite3.Connection,
        seed: int = 2031,
    ):
        self.connection = connection
        self.cursor = connection.cursor()
        self.random = random.Random(seed)

    def generate(
        self,
        team_ids: dict[str, int],
    ) -> int:
        self._delete_unassigned_players()

        player_count = 0

        for club_index, club in enumerate(
            DEMO_CLUBS,
            start=1,
        ):
            team_id = team_ids.get(club.name)

            if team_id is None:
                raise ValueError(
                    "Keine Mannschaft für Verein gefunden: "
                    f"{club.name}"
                )

            self._delete_team_players(team_id)

            club_strength = 55 + club_index * 2

            players = generate_players_for_club(
                club_strength,
                club_index,
            )

            for player in players:
                height_cm = self._generate_height(
                    player.position
                )

                weight_kg = self._generate_weight(
                    height_cm,
                    player.position,
                )

                self.cursor.execute(
                    """
                    INSERT INTO players (
                        team_id,
                        first_name,
                        last_name,
                        birthdate,
                        position,
                        shirt_number,
                        foot,
                        height_cm,
                        weight_kg,
                        nationality,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        team_id,
                        player.first_name,
                        player.last_name,
                        player.birthdate,
                        player.position,
                        player.number,
                        player.foot,
                        height_cm,
                        weight_kg,
                        "Deutschland",
                        1,
                    ),
                )

                player_count += 1

        return player_count

    def _delete_unassigned_players(self):
        self.cursor.execute(
            """
            DELETE FROM players
            WHERE team_id IS NULL
            """
        )

    def _delete_team_players(
        self,
        team_id: int,
    ):
        self.cursor.execute(
            """
            DELETE FROM players
            WHERE team_id = ?
            """,
            (team_id,),
        )

    def _generate_height(
        self,
        position: str,
    ) -> int:
        if position == "Torwart":
            return self.random.randint(184, 198)

        if position in {
            "Innenverteidiger",
            "Stürmer",
        }:
            return self.random.randint(178, 194)

        return self.random.randint(168, 190)

    def _generate_weight(
        self,
        height_cm: int,
        position: str,
    ) -> int:
        base_weight = height_cm - 105

        if position in {
            "Torwart",
            "Innenverteidiger",
        }:
            base_weight += self.random.randint(4, 10)
        else:
            base_weight += self.random.randint(0, 7)

        return max(
            58,
            min(100, base_weight),
        )