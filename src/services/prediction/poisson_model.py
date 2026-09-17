from __future__ import annotations

import math
from dataclasses import dataclass

from src.services.prediction.form_service import TeamForm
from src.services.prediction.lineup_strength_service import (
    LineupStrength,
)
from src.services.prediction.opponent_strength_service import (
    OpponentStrength,
)
from src.services.prediction.player_strength_service import (
    TeamPlayerStrength,
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
class ExpectedGoalsStep:
    name: str
    home: float
    away: float


@dataclass(frozen=True, slots=True)
class ExpectedGoalsBreakdown:
    league_average_home_goals: float
    league_average_away_goals: float

    home_attack_strength: float
    home_defense_strength: float
    away_attack_strength: float
    away_defense_strength: float

    home_form_factor: float
    away_form_factor: float

    home_opponent_factor: float
    away_opponent_factor: float

    home_player_factor: float
    away_player_factor: float

    home_lineup_factor: float
    away_lineup_factor: float

    steps: tuple[ExpectedGoalsStep, ...]

    final_expected_goals: ExpectedGoals


@dataclass(frozen=True, slots=True)
class PoissonPrediction:
    expected_goals: ExpectedGoals
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    score_probabilities: tuple[ScoreProbability, ...]

    @property
    def most_likely_scores(
        self,
    ) -> tuple[ScoreProbability, ...]:
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
        player_strength_weight: float = 0.0,
        lineup_strength_weight: float = 0.75,
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

        if not 0.0 <= player_strength_weight <= 2.0:
            raise ValueError(
                "player_strength_weight muss zwischen "
                "0.0 und 2.0 liegen."
            )

        if not 0.0 <= lineup_strength_weight <= 1.5:
            raise ValueError(
                "lineup_strength_weight muss zwischen "
                "0.0 und 1.5 liegen."
            )

        self.max_goals = max_goals
        self.form_weight = form_weight
        self.opponent_strength_weight = (
            opponent_strength_weight
        )
        self.player_strength_weight = (
            player_strength_weight
        )
        self.lineup_strength_weight = (
            lineup_strength_weight
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
        home_player_strength: TeamPlayerStrength | None = None,
        away_player_strength: TeamPlayerStrength | None = None,
        home_lineup_strength: LineupStrength | None = None,
        away_lineup_strength: LineupStrength | None = None,
    ) -> PoissonPrediction:
        expected = self.calculate_expected_goals(
            home_team=home_team,
            away_team=away_team,
            league=league,
            home_form=home_form,
            away_form=away_form,
            home_opponent_strength=home_opponent_strength,
            away_opponent_strength=away_opponent_strength,
            home_player_strength=home_player_strength,
            away_player_strength=away_player_strength,
            home_lineup_strength=home_lineup_strength,
            away_lineup_strength=away_lineup_strength,
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

        total = (
            home_win
            + draw
            + away_win
        )

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
                probability=(
                    item.probability
                    / total
                ),
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
        home_player_strength: TeamPlayerStrength | None = None,
        away_player_strength: TeamPlayerStrength | None = None,
        home_lineup_strength: LineupStrength | None = None,
        away_lineup_strength: LineupStrength | None = None,
    ) -> ExpectedGoals:
        breakdown = (
            self.calculate_expected_goals_breakdown(
                home_team=home_team,
                away_team=away_team,
                league=league,
                home_form=home_form,
                away_form=away_form,
                home_opponent_strength=home_opponent_strength,
                away_opponent_strength=away_opponent_strength,
                home_player_strength=home_player_strength,
                away_player_strength=away_player_strength,
                home_lineup_strength=home_lineup_strength,
                away_lineup_strength=away_lineup_strength,
            )
        )

        return breakdown.final_expected_goals

    def calculate_expected_goals_breakdown(
        self,
        home_team: TeamStrength,
        away_team: TeamStrength,
        league: LeagueStrength,
        home_form: TeamForm | None = None,
        away_form: TeamForm | None = None,
        home_opponent_strength: OpponentStrength | None = None,
        away_opponent_strength: OpponentStrength | None = None,
        home_player_strength: TeamPlayerStrength | None = None,
        away_player_strength: TeamPlayerStrength | None = None,
        home_lineup_strength: LineupStrength | None = None,
        away_lineup_strength: LineupStrength | None = None,
    ) -> ExpectedGoalsBreakdown:
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

        steps: list[ExpectedGoalsStep] = [
            ExpectedGoalsStep(
                name="Teamstärke",
                home=home_expected,
                away=away_expected,
            )
        ]

        home_form_factor = 1.0
        away_form_factor = 1.0

        if (
            self.form_weight > 0.0
            and home_form is not None
            and away_form is not None
        ):
            raw_home_form_factor = (
                home_form.attack_factor
                * away_form.defense_factor
            )

            raw_away_form_factor = (
                away_form.attack_factor
                * home_form.defense_factor
            )

            home_form_factor = (
                self._blend_factor(
                    raw_home_form_factor
                )
            )

            away_form_factor = (
                self._blend_factor(
                    raw_away_form_factor
                )
            )

            home_expected *= (
                home_form_factor
            )

            away_expected *= (
                away_form_factor
            )

        steps.append(
            ExpectedGoalsStep(
                name="Form",
                home=home_expected,
                away=away_expected,
            )
        )

        home_opponent_factor = 1.0
        away_opponent_factor = 1.0

        if (
            self.opponent_strength_weight > 0.0
            and home_opponent_strength is not None
            and away_opponent_strength is not None
        ):
            home_opponent_factor = (
                self._blend_opponent_strength(
                    home_opponent_strength.schedule_factor
                )
            )

            away_opponent_factor = (
                self._blend_opponent_strength(
                    away_opponent_strength.schedule_factor
                )
            )

            home_expected *= (
                home_opponent_factor
            )

            away_expected *= (
                away_opponent_factor
            )

        steps.append(
            ExpectedGoalsStep(
                name="Gegnerstärke",
                home=home_expected,
                away=away_expected,
            )
        )

        home_player_factor = 1.0
        away_player_factor = 1.0

        if (
            self.player_strength_weight > 0.0
            and home_player_strength is not None
            and away_player_strength is not None
        ):
            home_player_factor = (
                self._blend_player_strength(
                    home_player_strength
                    .relative_team_player_factor
                )
            )

            away_player_factor = (
                self._blend_player_strength(
                    away_player_strength
                    .relative_team_player_factor
                )
            )

            home_expected *= (
                home_player_factor
            )

            away_expected *= (
                away_player_factor
            )

        steps.append(
            ExpectedGoalsStep(
                name="Spielerstärke",
                home=home_expected,
                away=away_expected,
            )
        )

        home_lineup_factor = 1.0
        away_lineup_factor = 1.0

        if (
            self.lineup_strength_weight > 0.0
            and home_lineup_strength is not None
            and away_lineup_strength is not None
        ):
            home_lineup_factor = (
                self._blend_lineup_strength(
                    home_lineup_strength
                    .relative_lineup_factor
                )
            )

            away_lineup_factor = (
                self._blend_lineup_strength(
                    away_lineup_strength
                    .relative_lineup_factor
                )
            )

            home_expected *= (
                home_lineup_factor
            )

            away_expected *= (
                away_lineup_factor
            )

        steps.append(
            ExpectedGoalsStep(
                name="Startelf",
                home=home_expected,
                away=away_expected,
            )
        )

        final_expected = ExpectedGoals(
            home=max(
                home_expected,
                0.0,
            ),
            away=max(
                away_expected,
                0.0,
            ),
        )

        return ExpectedGoalsBreakdown(
            league_average_home_goals=(
                league.average_home_goals
            ),
            league_average_away_goals=(
                league.average_away_goals
            ),
            home_attack_strength=(
                home_team.home_attack_strength
            ),
            home_defense_strength=(
                home_team.home_defense_strength
            ),
            away_attack_strength=(
                away_team.away_attack_strength
            ),
            away_defense_strength=(
                away_team.away_defense_strength
            ),
            home_form_factor=(
                home_form_factor
            ),
            away_form_factor=(
                away_form_factor
            ),
            home_opponent_factor=(
                home_opponent_factor
            ),
            away_opponent_factor=(
                away_opponent_factor
            ),
            home_player_factor=(
                home_player_factor
            ),
            away_player_factor=(
                away_player_factor
            ),
            home_lineup_factor=(
                home_lineup_factor
            ),
            away_lineup_factor=(
                away_lineup_factor
            ),
            steps=tuple(
                steps
            ),
            final_expected_goals=(
                final_expected
            ),
        )

    def _blend_factor(
        self,
        form_factor: float,
    ) -> float:
        return (
            (1.0 - self.form_weight)
            + self.form_weight
            * form_factor
        )

    def _blend_opponent_strength(
        self,
        schedule_factor: float,
    ) -> float:
        return (
            (
                1.0
                - self.opponent_strength_weight
            )
            + self.opponent_strength_weight
            * schedule_factor
        )

    def _blend_player_strength(
        self,
        relative_factor: float,
    ) -> float:
        return (
            (
                1.0
                - self.player_strength_weight
            )
            + self.player_strength_weight
            * relative_factor
        )

    def _blend_lineup_strength(
        self,
        relative_factor: float,
    ) -> float:
        return (
            (
                1.0
                - self.lineup_strength_weight
            )
            + self.lineup_strength_weight
            * relative_factor
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
            for goals in range(
                self.max_goals + 1
            )
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
            math.exp(
                -expected_goals
            )
            * expected_goals**goals
            / math.factorial(
                goals
            )
        )