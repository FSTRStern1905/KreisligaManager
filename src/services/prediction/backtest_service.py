from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.form_service import FormService
from src.services.prediction.historical_data_context import HistoricalDataContext
from src.services.prediction.poisson_model import PoissonModel
from src.services.prediction.opponent_strength_service import (
    OpponentStrengthService,
)
from src.services.prediction.prediction_models import (
    BacktestMatchResult,
    MatchPrediction,
)
from src.services.prediction.team_strength_service import TeamStrengthService


@dataclass(frozen=True, slots=True)
class MatchdayBacktestResult:
    matchday: int
    matches: tuple[BacktestMatchResult, ...]

    @property
    def matches_tested(self) -> int:
        return len(self.matches)

    @property
    def correct_outcomes(self) -> int:
        return sum(
            1
            for match in self.matches
            if match.outcome_correct
        )

    @property
    def accuracy(self) -> float:
        if not self.matches:
            return 0.0

        return self.correct_outcomes / len(self.matches)

    @property
    def average_brier_score(self) -> float:
        if not self.matches:
            return 0.0

        return sum(
            match.brier_score
            for match in self.matches
        ) / len(self.matches)


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    competition_id: int
    start_matchday: int
    end_matchday: int
    matchdays: tuple[MatchdayBacktestResult, ...]

    @property
    def matches_tested(self) -> int:
        return sum(
            matchday.matches_tested
            for matchday in self.matchdays
        )

    @property
    def correct_outcomes(self) -> int:
        return sum(
            matchday.correct_outcomes
            for matchday in self.matchdays
        )

    @property
    def accuracy(self) -> float:
        if self.matches_tested == 0:
            return 0.0

        return self.correct_outcomes / self.matches_tested

    @property
    def average_brier_score(self) -> float:
        matches = [
            match
            for matchday in self.matchdays
            for match in matchday.matches
        ]

        if not matches:
            return 0.0

        return sum(
            match.brier_score
            for match in matches
        ) / len(matches)


class BacktestService:
    def __init__(
        self,
        connection,
        max_goals: int = 10,
        form_weight: float = 0.0,
        form_matches: int = 5,
        opponent_strength_weight: float = 0.0,
    ) -> None:
        if form_matches <= 0:
            raise ValueError(
                "form_matches muss größer als 0 sein."
            )

        self.connection = connection
        self.form_matches = form_matches
        self.poisson_model = PoissonModel(
            max_goals=max_goals,
            form_weight=form_weight,
            opponent_strength_weight=(
                opponent_strength_weight
            ),
        )

    def run(
        self,
        competition_id: int,
        start_matchday: int = 5,
        end_matchday: int | None = None,
    ) -> BacktestSummary:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if start_matchday < 2:
            raise ValueError(
                "Der Backtest muss frühestens ab Spieltag 2 starten."
            )

        if end_matchday is None:
            end_matchday = self._get_last_matchday(
                competition_id
            )

        if end_matchday < start_matchday:
            raise ValueError(
                "Endspieltag liegt vor Startspieltag."
            )

        results: list[MatchdayBacktestResult] = []

        for matchday in range(
            start_matchday,
            end_matchday + 1,
        ):
            result = self._backtest_matchday(
                competition_id=competition_id,
                matchday=matchday,
            )

            if result.matches:
                results.append(result)

        return BacktestSummary(
            competition_id=competition_id,
            start_matchday=start_matchday,
            end_matchday=end_matchday,
            matchdays=tuple(results),
        )

    def _backtest_matchday(
        self,
        competition_id: int,
        matchday: int,
    ) -> MatchdayBacktestResult:
        context = HistoricalDataContext(
            connection=self.connection,
            competition_id=competition_id,
            cutoff_matchday=matchday,
        )

        strength_service = TeamStrengthService(context)
        form_service = FormService(context)
        opponent_strength_service = (
            OpponentStrengthService(context)
        )
        league = strength_service.get_league_strength()

        fixtures = self._get_finished_matches(
            competition_id=competition_id,
            matchday=matchday,
        )

        results: list[BacktestMatchResult] = []

        for fixture in fixtures:
            home_strength = strength_service.get_team_strength(
                fixture["home_team_id"]
            )
            away_strength = strength_service.get_team_strength(
                fixture["away_team_id"]
            )

            home_form = form_service.get_team_form(
                fixture["home_team_id"],
                last_matches=self.form_matches,
            )
            away_form = form_service.get_team_form(
                fixture["away_team_id"],
                last_matches=self.form_matches,
            )

            home_opponent_strength = (
                opponent_strength_service
                .get_team_opponent_strength(
                    fixture["home_team_id"]
                )
            )
            away_opponent_strength = (
                opponent_strength_service
                .get_team_opponent_strength(
                    fixture["away_team_id"]
                )
            )

            poisson_prediction = self.poisson_model.predict(
                home_team=home_strength,
                away_team=away_strength,
                league=league,
                home_form=home_form,
                away_form=away_form,
                home_opponent_strength=(
                    home_opponent_strength
                ),
                away_opponent_strength=(
                    away_opponent_strength
                ),
            )

            prediction = MatchPrediction(
                match_id=fixture["match_id"],
                competition_id=competition_id,
                cutoff_matchday=matchday,
                home_team_id=fixture["home_team_id"],
                away_team_id=fixture["away_team_id"],
                home_team_name=fixture["home_team_name"],
                away_team_name=fixture["away_team_name"],
                expected_home_goals=poisson_prediction.expected_goals.home,
                expected_away_goals=poisson_prediction.expected_goals.away,
                home_win_probability=poisson_prediction.home_win_probability,
                draw_probability=poisson_prediction.draw_probability,
                away_win_probability=poisson_prediction.away_win_probability,
                most_likely_scores=poisson_prediction.most_likely_scores,
            )

            results.append(
                BacktestMatchResult(
                    prediction=prediction,
                    actual_home_goals=fixture["home_goals"],
                    actual_away_goals=fixture["away_goals"],
                )
            )

        return MatchdayBacktestResult(
            matchday=matchday,
            matches=tuple(results),
        )

    def _get_finished_matches(
        self,
        competition_id: int,
        matchday: int,
    ) -> list[dict]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                matches.match_id,
                matches.home_team_id,
                matches.away_team_id,
                matches.home_goals,
                matches.away_goals,
                home_team.name AS home_team_name,
                away_team.name AS away_team_name
            FROM matches
            INNER JOIN teams AS home_team
                ON home_team.team_id = matches.home_team_id
            INNER JOIN teams AS away_team
                ON away_team.team_id = matches.away_team_id
            WHERE
                matches.competition_id = ?
                AND matches.matchday = ?
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL
            ORDER BY matches.match_id;
            """,
            (competition_id, matchday),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def _get_last_matchday(
        self,
        competition_id: int,
    ) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT MAX(matchday)
            FROM matches
            WHERE
                competition_id = ?
                AND matchday IS NOT NULL;
            """,
            (competition_id,),
        )

        row = cursor.fetchone()

        if row is None or row[0] is None:
            raise ValueError(
                "Keine Spieltage für den Wettbewerb gefunden."
            )

        return int(row[0])
