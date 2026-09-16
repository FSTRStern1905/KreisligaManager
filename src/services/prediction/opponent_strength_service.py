from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.team_strength_service import (
    TeamStrengthService,
)


@dataclass(frozen=True, slots=True)
class OpponentStrength:
    team_id: int
    matches_used: int
    average_opponent_strength: float
    average_opponent_attack: float
    average_opponent_defense: float
    schedule_factor: float


class OpponentStrengthService:
    """
    Berechnet die bisherige Gegnerstärke eines Teams ausschließlich
    aus dem HistoricalDataContext.

    Werte:
    - 1.0 = durchschnittliche Gegner
    - >1.0 = überdurchschnittlich starke Gegner
    - <1.0 = unterdurchschnittlich starke Gegner

    Der Stichtag-Schutz bleibt erhalten, da ausschließlich bereits
    bekannte historische Spiele aus dem Context verwendet werden.
    """

    SMOOTHING_MATCHES = 5.0

    def __init__(
        self,
        context: HistoricalDataContext,
    ) -> None:
        self.context = context
        self.strength_service = TeamStrengthService(
            context
        )
        self._strength_cache: dict[int, object] = {}

    def get_team_opponent_strength(
        self,
        team_id: int,
    ) -> OpponentStrength:
        matches = self.context.get_team_matches(
            team_id
        )

        if not matches:
            return OpponentStrength(
                team_id=team_id,
                matches_used=0,
                average_opponent_strength=1.0,
                average_opponent_attack=1.0,
                average_opponent_defense=1.0,
                schedule_factor=1.0,
            )

        opponent_strengths: list[float] = []
        opponent_attacks: list[float] = []
        opponent_defenses: list[float] = []

        for match in matches:
            opponent_id = self._opponent_id(
                match=match,
                team_id=team_id,
            )

            strength = self._get_strength(
                opponent_id
            )

            opponent_attack = (
                strength.attack_strength
            )
            opponent_defense = (
                strength.defense_strength
            )

            combined_strength = (
                opponent_attack
                + self._inverse_defense_strength(
                    opponent_defense
                )
            ) / 2.0

            opponent_strengths.append(
                combined_strength
            )
            opponent_attacks.append(
                opponent_attack
            )
            opponent_defenses.append(
                opponent_defense
            )

        matches_used = len(opponent_strengths)

        average_opponent_strength = (
            sum(opponent_strengths)
            / matches_used
        )
        average_opponent_attack = (
            sum(opponent_attacks)
            / matches_used
        )
        average_opponent_defense = (
            sum(opponent_defenses)
            / matches_used
        )

        schedule_factor = self._smooth_factor(
            factor=average_opponent_strength,
            matches_used=matches_used,
        )

        return OpponentStrength(
            team_id=team_id,
            matches_used=matches_used,
            average_opponent_strength=(
                average_opponent_strength
            ),
            average_opponent_attack=(
                average_opponent_attack
            ),
            average_opponent_defense=(
                average_opponent_defense
            ),
            schedule_factor=schedule_factor,
        )

    def _get_strength(
        self,
        team_id: int,
    ):
        if team_id not in self._strength_cache:
            self._strength_cache[team_id] = (
                self.strength_service.get_team_strength(
                    team_id
                )
            )

        return self._strength_cache[team_id]

    def _smooth_factor(
        self,
        factor: float,
        matches_used: int,
    ) -> float:
        if matches_used <= 0:
            return 1.0

        weight = (
            matches_used
            / (
                matches_used
                + self.SMOOTHING_MATCHES
            )
        )

        return (
            weight * factor
            + (1.0 - weight) * 1.0
        )

    @staticmethod
    def _inverse_defense_strength(
        defense_strength: float,
    ) -> float:
        if defense_strength <= 0.0:
            return 1.0

        return 1.0 / defense_strength

    @staticmethod
    def _opponent_id(
        match,
        team_id: int,
    ) -> int:
        if match.home_team_id == team_id:
            return match.away_team_id

        if match.away_team_id == team_id:
            return match.home_team_id

        raise ValueError(
            "Das Spiel gehört nicht zum angegebenen Team."
        )
