from __future__ import annotations

import math
from dataclasses import dataclass

from src.services.prediction.form_service import TeamForm
from src.services.prediction.opponent_strength_service import (
    OpponentStrength,
)
from src.services.prediction.prediction_models import ScoreProbability
from src.services.prediction.team_strength_service import (
    LeagueStrength,
    TeamStrength,
)


@dataclass(frozen=True, slots=True)
class ExpectedGoals:
    home: float
    away: float


@dataclass(frozen=True, slots=True)
class PoissonPrediction:
    expected_goals: ExpectedGoals
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    score_probabilities: tuple[ScoreProbability, ...]

    @property
    def most_likely_scores(self) -> tuple[ScoreProbability, ...]:
        return tuple(
            sorted(
                self.score_probabilities,
                key=lambda item: item.probability,
                reverse=True,
            )[:5]
        )


class PoissonModel:
    def __init__(
        self,
        max_goals: int = 10,
        form_weight: float = 0.0,
        opponent_strength_weight: float = 0.0,
    ) -> None:
        if max_goals < 5:
            raise ValueError(
                "max_goals muss mindestens 5 sein."
            )

        if not 0.0 <= form_weight <= 1.0:
            raise ValueError(
                "form_weight muss zwischen 0.0 und 1.0 liegen."
            )

        if not 0.0 <= opponent_strength_weight <= 2.0:
            raise ValueError(
                "opponent_strength_weight muss zwischen "
                "0.0 und 2.0 liegen."
            )

        self.max_goals = max_goals
        self.form_weight = form_weight
        self.opponent_strength_weight = (
            opponent_strength_weight
        )

    def predict(
        self,
        home_team: TeamStrength,
        away_team: TeamStrength,
        league: LeagueStrength,
        home_form: TeamForm | None = None,
        away_form: TeamForm | None = None,
        home_opponent_strength: OpponentStrength | None = None,
        away_opponent_strength: OpponentStrength | None = None,
    ) -> PoissonPrediction:
        expected = self.calculate_expected_goals(
            home_team=home_team,
            away_team=away_team,
            league=league,
            home_form=home_form,
            away_form=away_form,
            home_opponent_strength=home_opponent_strength,
            away_opponent_strength=away_opponent_strength,
        )

        home_distribution = self._distribution(
            expected.home
        )
        away_distribution = self._distribution(
            expected.away
        )

        scores: list[ScoreProbability] = []
        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for home_goals, home_probability in enumerate(
            home_distribution
        ):
            for away_goals, away_probability in enumerate(
                away_distribution
            ):
                probability = (
                    home_probability
                    * away_probability
                )

                scores.append(
                    ScoreProbability(
                        home_goals=home_goals,
                        away_goals=away_goals,
                        probability=probability,
                    )
                )

                if home_goals > away_goals:
                    home_win += probability
                elif home_goals < away_goals:
                    away_win += probability
                else:
                    draw += probability

        total = home_win + draw + away_win

        if total <= 0.0:
            raise RuntimeError(
                "Poisson-Wahrscheinlichkeiten konnten "
                "nicht berechnet werden."
            )

        home_win /= total
        draw /= total
        away_win /= total

        normalized_scores = tuple(
            ScoreProbability(
                home_goals=item.home_goals,
                away_goals=item.away_goals,
                probability=item.probability / total,
            )
            for item in scores
        )

        return PoissonPrediction(
            expected_goals=expected,
            home_win_probability=home_win,
            draw_probability=draw,
            away_win_probability=away_win,
            score_probabilities=normalized_scores,
        )

    def calculate_expected_goals(
        self,
        home_team: TeamStrength,
        away_team: TeamStrength,
        league: LeagueStrength,
        home_form: TeamForm | None = None,
        away_form: TeamForm | None = None,
        home_opponent_strength: OpponentStrength | None = None,
        away_opponent_strength: OpponentStrength | None = None,
    ) -> ExpectedGoals:
        if league.matches_played <= 0:
            raise ValueError(
                "Keine historischen Ligaspiele vorhanden."
            )

        home_expected = (
            league.average_home_goals
            * home_team.home_attack_strength
            * away_team.away_defense_strength
        )

        away_expected = (
            league.average_away_goals
            * away_team.away_attack_strength
            * home_team.home_defense_strength
        )

        if (
            self.form_weight > 0.0
            and home_form is not None
            and away_form is not None
        ):
            home_form_factor = (
                home_form.attack_factor
                * away_form.defense_factor
            )
            away_form_factor = (
                away_form.attack_factor
                * home_form.defense_factor
            )

            home_expected *= self._blend_factor(
                home_form_factor
            )
            away_expected *= self._blend_factor(
                away_form_factor
            )

        if (
            self.opponent_strength_weight > 0.0
            and home_opponent_strength is not None
            and away_opponent_strength is not None
        ):
            home_expected *= self._blend_opponent_strength(
                home_opponent_strength.schedule_factor
            )
            away_expected *= self._blend_opponent_strength(
                away_opponent_strength.schedule_factor
            )

        return ExpectedGoals(
            home=max(home_expected, 0.0),
            away=max(away_expected, 0.0),
        )

    def _blend_factor(
        self,
        form_factor: float,
    ) -> float:
        return (
            (1.0 - self.form_weight)
            + self.form_weight * form_factor
        )

    def _blend_opponent_strength(
        self,
        schedule_factor: float,
    ) -> float:
        return (
            (1.0 - self.opponent_strength_weight)
            + self.opponent_strength_weight
            * schedule_factor
        )

    def _distribution(
        self,
        expected_goals: float,
    ) -> tuple[float, ...]:
        return tuple(
            self._poisson_probability(
                goals=goals,
                expected_goals=expected_goals,
            )
            for goals in range(self.max_goals + 1)
        )

    @staticmethod
    def _poisson_probability(
        goals: int,
        expected_goals: float,
    ) -> float:
        if goals < 0:
            return 0.0

        if expected_goals < 0.0:
            raise ValueError(
                "Erwartete Tore dürfen nicht negativ sein."
            )

        return (
            math.exp(-expected_goals)
            * expected_goals**goals
            / math.factorial(goals)
        )
