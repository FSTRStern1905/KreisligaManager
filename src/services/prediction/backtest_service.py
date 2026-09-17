from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.form_service import FormService
from src.services.prediction.historical_data_context import HistoricalDataContext
from src.services.prediction.lineup_strength_service import LineupStrengthService
from src.services.prediction.opponent_strength_service import (
    OpponentStrengthService,
)
from src.services.prediction.player_strength_service import (
    PlayerStrengthService,
)
from src.services.prediction.poisson_model import PoissonModel
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

    @property
    def average_log_loss(self) -> float:
        if not self.matches:
            return 0.0
        return sum(
            match.log_loss
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

    @property
    def average_log_loss(self) -> float:
        matches = [
            match
            for matchday in self.matchdays
            for match in matchday.matches
        ]
        if not matches:
            return 0.0
        return sum(
            match.log_loss
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
        player_strength_weight: float = 0.0,
        player_core_size: int = 14,
        lineup_strength_weight: float = 0.75,
        minimum_lineup_players: int = 11,
        minimum_known_lineup_players: int = 8,
    ) -> None:
        if form_matches <= 0:
            raise ValueError(
                "form_matches muss größer als 0 sein."
            )

        if player_core_size <= 0:
            raise ValueError(
                "player_core_size muss größer als 0 sein."
            )

        if not 0 <= minimum_lineup_players <= 11:
            raise ValueError(
                "minimum_lineup_players muss zwischen 0 und 11 liegen."
            )

        if not 0 <= minimum_known_lineup_players <= 11:
            raise ValueError(
                "minimum_known_lineup_players muss zwischen 0 und 11 liegen."
            )

        self.connection = connection
        self.form_matches = form_matches
        self.player_core_size = player_core_size
        self.player_strength_weight = player_strength_weight
        self.lineup_strength_weight = lineup_strength_weight
        self.minimum_lineup_players = minimum_lineup_players
        self.minimum_known_lineup_players = (
            minimum_known_lineup_players
        )

        self.poisson_model = PoissonModel(
            max_goals=max_goals,
            form_weight=form_weight,
            opponent_strength_weight=(
                opponent_strength_weight
            ),
            player_strength_weight=(
                player_strength_weight
            ),
            lineup_strength_weight=(
                lineup_strength_weight
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

        player_strength_service = (
            PlayerStrengthService(context)
            if self.player_strength_weight > 0.0
            else None
        )

        lineup_strength_service = (
            LineupStrengthService(context)
            if self.lineup_strength_weight > 0.0
            else None
        )

        league = strength_service.get_league_strength()

        fixtures = self._get_finished_matches(
            competition_id=competition_id,
            matchday=matchday,
        )

        results: list[BacktestMatchResult] = []

        for fixture in fixtures:
            home_team_id = fixture["home_team_id"]
            away_team_id = fixture["away_team_id"]

            home_strength = strength_service.get_team_strength(
                home_team_id
            )
            away_strength = strength_service.get_team_strength(
                away_team_id
            )

            home_form = form_service.get_team_form(
                home_team_id,
                last_matches=self.form_matches,
            )
            away_form = form_service.get_team_form(
                away_team_id,
                last_matches=self.form_matches,
            )

            home_opponent_strength = (
                opponent_strength_service
                .get_team_opponent_strength(
                    home_team_id
                )
            )
            away_opponent_strength = (
                opponent_strength_service
                .get_team_opponent_strength(
                    away_team_id
                )
            )

            home_player_strength = None
            away_player_strength = None

            if player_strength_service is not None:
                home_player_strength = (
                    player_strength_service
                    .get_team_player_strength(
                        home_team_id,
                        core_size=self.player_core_size,
                    )
                )
                away_player_strength = (
                    player_strength_service
                    .get_team_player_strength(
                        away_team_id,
                        core_size=self.player_core_size,
                    )
                )

            home_lineup_strength = None
            away_lineup_strength = None

            if lineup_strength_service is not None:
                home_lineup_strength = (
                    lineup_strength_service.get_lineup_strength(
                        match_id=fixture["match_id"],
                        team_id=home_team_id,
                    )
                )
                away_lineup_strength = (
                    lineup_strength_service.get_lineup_strength(
                        match_id=fixture["match_id"],
                        team_id=away_team_id,
                    )
                )

                if not self._lineup_is_usable(
                    home_lineup_strength
                ):
                    continue

                if not self._lineup_is_usable(
                    away_lineup_strength
                ):
                    continue

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
                home_player_strength=(
                    home_player_strength
                ),
                away_player_strength=(
                    away_player_strength
                ),
                home_lineup_strength=(
                    home_lineup_strength
                ),
                away_lineup_strength=(
                    away_lineup_strength
                ),
            )

            prediction = MatchPrediction(
                match_id=fixture["match_id"],
                competition_id=competition_id,
                cutoff_matchday=matchday,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=fixture["home_team_name"],
                away_team_name=fixture["away_team_name"],
                expected_home_goals=(
                    poisson_prediction.expected_goals.home
                ),
                expected_away_goals=(
                    poisson_prediction.expected_goals.away
                ),
                home_win_probability=(
                    poisson_prediction.home_win_probability
                ),
                draw_probability=(
                    poisson_prediction.draw_probability
                ),
                away_win_probability=(
                    poisson_prediction.away_win_probability
                ),
                most_likely_scores=(
                    poisson_prediction.most_likely_scores
                ),
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

    def _lineup_is_usable(
        self,
        lineup_strength,
    ) -> bool:
        if (
            lineup_strength.lineup_players
            < self.minimum_lineup_players
        ):
            return False

        if (
            lineup_strength.known_players
            < self.minimum_known_lineup_players
        ):
            return False

        return True

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
            ORDER BY
                matches.match_id
            """,
            (
                competition_id,
                matchday,
            ),
        )

        return [
            {
                "match_id": int(row[0]),
                "home_team_id": int(row[1]),
                "away_team_id": int(row[2]),
                "home_goals": int(row[3]),
                "away_goals": int(row[4]),
                "home_team_name": str(row[5]),
                "away_team_name": str(row[6]),
            }
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
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            """,
            (competition_id,),
        )

        row = cursor.fetchone()

        if (
            row is None
            or row[0] is None
        ):
            raise ValueError(
                "Keine abgeschlossenen Spiele vorhanden."
            )

        return int(row[0])
