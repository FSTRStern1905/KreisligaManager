import random
import sqlite3

from src.demo.event_generator import DemoEventGenerator


class DemoCardGenerator(DemoEventGenerator):
    YELLOW_CARD = "YELLOW_CARD"
    YELLOW_RED_CARD = "YELLOW_RED_CARD"
    RED_CARD = "RED_CARD"

    def __init__(
        self,
        connection: sqlite3.Connection,
        seed: int = 2030,
    ):
        super().__init__(connection)

        self.random = random.Random(seed)

    def generate_for_competition(
        self,
        competition_id: int,
    ) -> dict:
        matches = self.load_finished_matches(
            competition_id
        )

        if not matches:
            raise ValueError(
                "Keine beendeten Spiele gefunden."
            )

        self.delete_events(
            competition_id,
            [
                self.YELLOW_CARD,
                self.YELLOW_RED_CARD,
                self.RED_CARD,
            ],
        )

        yellow_id = self.get_event_type_id(
            self.YELLOW_CARD
        )

        yellow_red_id = self.get_event_type_id(
            self.YELLOW_RED_CARD
        )

        red_id = self.get_event_type_id(
            self.RED_CARD
        )

        yellow_count = 0
        yellow_red_count = 0
        red_count = 0

        for (
            match_id,
            home_team,
            away_team,
            _,
            _,
        ) in matches:

            yellow_count += self._generate_team_cards(
                match_id,
                home_team,
                yellow_id,
            )

            yellow_count += self._generate_team_cards(
                match_id,
                away_team,
                yellow_id,
            )

            yellow_red_count += (
                self._generate_special_card(
                    match_id,
                    home_team,
                    yellow_red_id,
                    probability=0.05,
                )
            )

            yellow_red_count += (
                self._generate_special_card(
                    match_id,
                    away_team,
                    yellow_red_id,
                    probability=0.05,
                )
            )

            red_count += self._generate_special_card(
                match_id,
                home_team,
                red_id,
                probability=0.03,
            )

            red_count += self._generate_special_card(
                match_id,
                away_team,
                red_id,
                probability=0.03,
            )

        self.commit()

        return {
            "matches": len(matches),
            "yellow_cards": yellow_count,
            "yellow_red_cards": yellow_red_count,
            "red_cards": red_count,
        }

    def _generate_team_cards(
        self,
        match_id: int,
        team_id: int,
        event_type_id: int,
    ) -> int:
        players = self.load_active_players(
            team_id
        )

        if not players:
            return 0

        card_count = self.random.randint(
            1,
            4,
        )

        for _ in range(card_count):
            player_id = self._choose_player(
                players
            )

            self.insert_event(
                match_id=match_id,
                event_type_id=event_type_id,
                minute=self.random.randint(1, 90),
                second=0,
                team_id=team_id,
                player_id=player_id,
                notes="Demo Gelbe Karte",
            )

        return card_count

    def _generate_special_card(
        self,
        match_id: int,
        team_id: int,
        event_type_id: int,
        probability: float,
    ) -> int:
        if self.random.random() > probability:
            return 0

        players = self.load_active_players(
            team_id
        )

        if not players:
            return 0

        player_id = self._choose_player(
            players
        )

        self.insert_event(
            match_id=match_id,
            event_type_id=event_type_id,
            minute=self.random.randint(1, 90),
            second=0,
            team_id=team_id,
            player_id=player_id,
        )

        return 1

    def _choose_player(
        self,
        players: list[tuple],
    ) -> int:
        player_ids = []
        weights = []

        for (
            player_id,
            position,
            shirt_number,
        ) in players:

            player_ids.append(player_id)

            weights.append(
                self._card_weight(
                    position
                )
            )

        return self.random.choices(
            player_ids,
            weights=weights,
            k=1,
        )[0]

    def _card_weight(
        self,
        position: str | None,
    ) -> int:
        weights = {
            "Torwart": 1,
            "Innenverteidiger": 12,
            "Außenverteidiger": 10,
            "Defensives Mittelfeld": 11,
            "Zentrales Mittelfeld": 8,
            "Offensives Mittelfeld": 6,
            "Flügel": 5,
            "Stürmer": 4,
        }

        return weights.get(
            position or "",
            6,
        )