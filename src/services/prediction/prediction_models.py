from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ScoreProbability:
    home_goals: int
    away_goals: int
    probability: float

    def __post_init__(self) -> None:
        if self.home_goals < 0 or self.away_goals < 0:
            raise ValueError("Tore dürfen nicht negativ sein.")
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(
                "Wahrscheinlichkeit muss zwischen 0 und 1 liegen."
            )

    @property
    def score(self) -> str:
        return f"{self.home_goals}:{self.away_goals}"


@dataclass(frozen=True, slots=True)
class MatchPrediction:
    match_id: int
    competition_id: int
    cutoff_matchday: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    expected_home_goals: float
    expected_away_goals: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    most_likely_scores: tuple[ScoreProbability, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if self.match_id <= 0:
            raise ValueError("Ungültige Spiel-ID.")
        if self.competition_id <= 0:
            raise ValueError("Ungültige Wettbewerb-ID.")
        if self.cutoff_matchday <= 0:
            raise ValueError("Ungültiger Prognose-Stichtag.")
        if self.home_team_id <= 0 or self.away_team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")
        if self.home_team_id == self.away_team_id:
            raise ValueError(
                "Heim- und Auswärtsmannschaft müssen "
                "unterschiedlich sein."
            )
        if self.expected_home_goals < 0:
            raise ValueError(
                "Erwartete Heimtore dürfen nicht negativ sein."
            )
        if self.expected_away_goals < 0:
            raise ValueError(
                "Erwartete Auswärtstore dürfen nicht negativ sein."
            )

        probabilities = (
            self.home_win_probability,
            self.draw_probability,
            self.away_win_probability,
        )
        if any(
            not 0.0 <= probability <= 1.0
            for probability in probabilities
        ):
            raise ValueError(
                "1X2-Wahrscheinlichkeiten müssen zwischen "
                "0 und 1 liegen."
            )
        if abs(sum(probabilities) - 1.0) > 0.000001:
            raise ValueError(
                "1X2-Wahrscheinlichkeiten müssen zusammen 1 ergeben."
            )

    @property
    def predicted_outcome(self) -> str:
        probabilities = {
            "1": self.home_win_probability,
            "X": self.draw_probability,
            "2": self.away_win_probability,
        }
        return max(probabilities, key=probabilities.get)


@dataclass(frozen=True, slots=True)
class BacktestMatchResult:
    prediction: MatchPrediction
    actual_home_goals: int
    actual_away_goals: int

    def __post_init__(self) -> None:
        if self.actual_home_goals < 0 or self.actual_away_goals < 0:
            raise ValueError(
                "Tatsächliche Tore dürfen nicht negativ sein."
            )

    @property
    def actual_outcome(self) -> str:
        if self.actual_home_goals > self.actual_away_goals:
            return "1"
        if self.actual_home_goals < self.actual_away_goals:
            return "2"
        return "X"

    @property
    def outcome_correct(self) -> bool:
        return self.prediction.predicted_outcome == self.actual_outcome

    @property
    def brier_score(self) -> float:
        actual = {"1": 0.0, "X": 0.0, "2": 0.0}
        actual[self.actual_outcome] = 1.0

        predicted = {
            "1": self.prediction.home_win_probability,
            "X": self.prediction.draw_probability,
            "2": self.prediction.away_win_probability,
        }

        return sum(
            (predicted[outcome] - actual[outcome]) ** 2
            for outcome in ("1", "X", "2")
        )
