from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum

from src.services.prediction.form_service import FormService
from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.lineup_strength_service import (
    LineupStrengthService,
)
from src.services.prediction.opponent_strength_service import (
    OpponentStrengthService,
)
from src.services.prediction.poisson_model import (
    ExpectedGoalsBreakdown,
    PoissonModel,
)
from src.services.prediction.prediction_models import (
    MatchPrediction,
)
from src.services.prediction.team_strength_service import (
    TeamStrengthService,
)


class PredictionMode(str, Enum):
    PREMATCH = "prematch"
    LINEUP = "lineup"


@dataclass(frozen=True, slots=True)
class PredictionTargetMatch:
    match_id: int
    competition_id: int
    matchday: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str


@dataclass(frozen=True, slots=True)
class PredictionBreakdown:
    match_id: int
    competition_id: int
    cutoff_matchday: int

    home_team_id: int
    away_team_id: int

    home_team_name: str
    away_team_name: str

    mode: PredictionMode

    historical_matches: int

    details: ExpectedGoalsBreakdown


@dataclass(frozen=True, slots=True)
class _PredictionComponents:
    target: PredictionTargetMatch
    context: HistoricalDataContext

    league_strength: object

    home_team_strength: object
    away_team_strength: object

    home_form: object
    away_form: object

    home_opponent_strength: object
    away_opponent_strength: object

    home_lineup_strength: object | None
    away_lineup_strength: object | None

    lineup_weight: float


class PredictionService:
    """
    Zentrale Schnittstelle der Prediction Engine.

    PREMATCH:
    - ausschließlich Daten vor dem Zielspieltag
    - keine tatsächliche Startelf des Zielspiels

    LINEUP:
    - gleiche historische Datengrundlage wie PREMATCH
    - zusätzlich tatsächliche Startelf des Zielspiels
    - Spielerbewertung weiterhin ausschließlich aus Daten
      vor dem Zielspieltag
    """

    FORM_MATCHES = 6

    FORM_WEIGHT = 0.20
    OPPONENT_STRENGTH_WEIGHT = 1.25

    # PREMATCH Player Strength brachte im Backtest
    # keinen messbaren Mehrwert.
    PLAYER_STRENGTH_WEIGHT = 0.0

    PREMATCH_LINEUP_WEIGHT = 0.0
    LINEUP_WEIGHT = 0.75

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

    def predict_match(
        self,
        match_id: int,
        mode: PredictionMode | str = PredictionMode.PREMATCH,
    ) -> MatchPrediction:
        prediction_mode = self._normalize_mode(
            mode
        )

        components = self._build_components(
            match_id=match_id,
            mode=prediction_mode,
        )

        model = self._create_model(
            lineup_weight=(
                components.lineup_weight
            )
        )

        poisson_prediction = model.predict(
            home_team=(
                components.home_team_strength
            ),
            away_team=(
                components.away_team_strength
            ),
            league=(
                components.league_strength
            ),
            home_form=(
                components.home_form
            ),
            away_form=(
                components.away_form
            ),
            home_opponent_strength=(
                components.home_opponent_strength
            ),
            away_opponent_strength=(
                components.away_opponent_strength
            ),
            home_lineup_strength=(
                components.home_lineup_strength
            ),
            away_lineup_strength=(
                components.away_lineup_strength
            ),
        )

        target = components.target

        return MatchPrediction(
            match_id=target.match_id,
            competition_id=target.competition_id,
            cutoff_matchday=target.matchday,
            home_team_id=target.home_team_id,
            away_team_id=target.away_team_id,
            home_team_name=target.home_team_name,
            away_team_name=target.away_team_name,
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

    def get_prediction_breakdown(
        self,
        match_id: int,
        mode: PredictionMode | str = PredictionMode.PREMATCH,
    ) -> PredictionBreakdown:
        prediction_mode = self._normalize_mode(
            mode
        )

        components = self._build_components(
            match_id=match_id,
            mode=prediction_mode,
        )

        model = self._create_model(
            lineup_weight=(
                components.lineup_weight
            )
        )

        details = (
            model.calculate_expected_goals_breakdown(
                home_team=(
                    components.home_team_strength
                ),
                away_team=(
                    components.away_team_strength
                ),
                league=(
                    components.league_strength
                ),
                home_form=(
                    components.home_form
                ),
                away_form=(
                    components.away_form
                ),
                home_opponent_strength=(
                    components.home_opponent_strength
                ),
                away_opponent_strength=(
                    components.away_opponent_strength
                ),
                home_lineup_strength=(
                    components.home_lineup_strength
                ),
                away_lineup_strength=(
                    components.away_lineup_strength
                ),
            )
        )

        target = components.target

        return PredictionBreakdown(
            match_id=target.match_id,
            competition_id=target.competition_id,
            cutoff_matchday=target.matchday,
            home_team_id=target.home_team_id,
            away_team_id=target.away_team_id,
            home_team_name=target.home_team_name,
            away_team_name=target.away_team_name,
            mode=prediction_mode,
            historical_matches=len(
                components.context.get_matches()
            ),
            details=details,
        )

    def _build_components(
        self,
        match_id: int,
        mode: PredictionMode,
    ) -> _PredictionComponents:
        if match_id <= 0:
            raise ValueError(
                "Ungültige Spiel-ID."
            )

        target = self._get_target_match(
            match_id
        )

        context = HistoricalDataContext(
            connection=self.connection,
            competition_id=(
                target.competition_id
            ),
            cutoff_matchday=(
                target.matchday
            ),
        )

        historical_matches = (
            context.get_matches()
        )

        if not historical_matches:
            raise ValueError(
                "Für dieses Spiel sind noch keine "
                "historischen Ligaspiele verfügbar."
            )

        team_strength_service = (
            TeamStrengthService(
                context
            )
        )

        form_service = FormService(
            context
        )

        opponent_strength_service = (
            OpponentStrengthService(
                context
            )
        )

        league_strength = (
            team_strength_service
            .get_league_strength()
        )

        home_team_strength = (
            team_strength_service
            .get_team_strength(
                target.home_team_id
            )
        )

        away_team_strength = (
            team_strength_service
            .get_team_strength(
                target.away_team_id
            )
        )

        home_form = (
            form_service.get_team_form(
                team_id=target.home_team_id,
                last_matches=self.FORM_MATCHES,
            )
        )

        away_form = (
            form_service.get_team_form(
                team_id=target.away_team_id,
                last_matches=self.FORM_MATCHES,
            )
        )

        home_opponent_strength = (
            opponent_strength_service
            .get_team_opponent_strength(
                target.home_team_id
            )
        )

        away_opponent_strength = (
            opponent_strength_service
            .get_team_opponent_strength(
                target.away_team_id
            )
        )

        home_lineup_strength = None
        away_lineup_strength = None

        lineup_weight = (
            self.PREMATCH_LINEUP_WEIGHT
        )

        if mode == PredictionMode.LINEUP:
            lineup_service = (
                LineupStrengthService(
                    context
                )
            )

            home_lineup_strength = (
                lineup_service
                .get_lineup_strength(
                    match_id=target.match_id,
                    team_id=target.home_team_id,
                )
            )

            away_lineup_strength = (
                lineup_service
                .get_lineup_strength(
                    match_id=target.match_id,
                    team_id=target.away_team_id,
                )
            )

            self._validate_lineup(
                team_name=(
                    target.home_team_name
                ),
                lineup_players=(
                    home_lineup_strength
                    .lineup_players
                ),
            )

            self._validate_lineup(
                team_name=(
                    target.away_team_name
                ),
                lineup_players=(
                    away_lineup_strength
                    .lineup_players
                ),
            )

            lineup_weight = (
                self.LINEUP_WEIGHT
            )

        return _PredictionComponents(
            target=target,
            context=context,
            league_strength=(
                league_strength
            ),
            home_team_strength=(
                home_team_strength
            ),
            away_team_strength=(
                away_team_strength
            ),
            home_form=home_form,
            away_form=away_form,
            home_opponent_strength=(
                home_opponent_strength
            ),
            away_opponent_strength=(
                away_opponent_strength
            ),
            home_lineup_strength=(
                home_lineup_strength
            ),
            away_lineup_strength=(
                away_lineup_strength
            ),
            lineup_weight=lineup_weight,
        )

    def _create_model(
        self,
        lineup_weight: float,
    ) -> PoissonModel:
        return PoissonModel(
            form_weight=(
                self.FORM_WEIGHT
            ),
            opponent_strength_weight=(
                self.OPPONENT_STRENGTH_WEIGHT
            ),
            player_strength_weight=(
                self.PLAYER_STRENGTH_WEIGHT
            ),
            lineup_strength_weight=(
                lineup_weight
            ),
        )

    def has_lineup(
        self,
        match_id: int,
    ) -> bool:
        target = self._get_target_match(
            match_id
        )

        return (
            self._count_starting_players(
                match_id=target.match_id,
                team_id=target.home_team_id,
            )
            > 0
            and self._count_starting_players(
                match_id=target.match_id,
                team_id=target.away_team_id,
            )
            > 0
        )

    def get_lineup_coverage(
        self,
        match_id: int,
    ) -> tuple[int, int]:
        target = self._get_target_match(
            match_id
        )

        home_players = (
            self._count_starting_players(
                match_id=target.match_id,
                team_id=target.home_team_id,
            )
        )

        away_players = (
            self._count_starting_players(
                match_id=target.match_id,
                team_id=target.away_team_id,
            )
        )

        return (
            home_players,
            away_players,
        )

    def _get_target_match(
        self,
        match_id: int,
    ) -> PredictionTargetMatch:
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                match_id,
                competition_id,
                matchday,
                home_team_id,
                away_team_id
            FROM matches
            WHERE match_id = ?;
            """,
            (
                match_id,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Spiel-ID {match_id} "
                "wurde nicht gefunden."
            )

        matchday = row[2]

        if matchday is None:
            raise ValueError(
                "Das Spiel besitzt keinen "
                "Spieltag."
            )

        home_team_id = int(
            row[3]
        )

        away_team_id = int(
            row[4]
        )

        return PredictionTargetMatch(
            match_id=int(
                row[0]
            ),
            competition_id=int(
                row[1]
            ),
            matchday=int(
                matchday
            ),
            home_team_id=(
                home_team_id
            ),
            away_team_id=(
                away_team_id
            ),
            home_team_name=(
                self._get_team_name(
                    home_team_id
                )
            ),
            away_team_name=(
                self._get_team_name(
                    away_team_id
                )
            ),
        )

    def _get_team_name(
        self,
        team_id: int,
    ) -> str:
        table_name = (
            self._find_team_table()
        )

        if table_name is None:
            return f"Team {team_id}"

        columns = (
            self._get_table_columns(
                table_name
            )
        )

        name_column = (
            self._find_name_column(
                columns
            )
        )

        if name_column is None:
            return f"Team {team_id}"

        id_column = (
            "team_id"
            if "team_id" in columns
            else "id"
            if "id" in columns
            else None
        )

        if id_column is None:
            return f"Team {team_id}"

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            SELECT "{name_column}"
            FROM "{table_name}"
            WHERE "{id_column}" = ?;
            """,
            (
                team_id,
            ),
        )

        row = cursor.fetchone()

        if (
            row is None
            or not row[0]
        ):
            return f"Team {team_id}"

        return str(
            row[0]
        ).strip()

    def _find_team_table(
        self,
    ) -> str | None:
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE
                type = 'table'
                AND name IN (
                    'teams',
                    'team'
                )
            ORDER BY
                CASE
                    WHEN name = 'teams'
                        THEN 0
                    ELSE 1
                END;
            """
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return str(
            row[0]
        )

    def _get_table_columns(
        self,
        table_name: str,
    ) -> set[str]:
        cursor = self.connection.cursor()

        cursor.execute(
            f'PRAGMA table_info("{table_name}");'
        )

        return {
            str(row[1])
            for row in cursor.fetchall()
        }

    @staticmethod
    def _find_name_column(
        columns: set[str],
    ) -> str | None:
        candidates = (
            "name",
            "team_name",
            "display_name",
            "short_name",
        )

        for candidate in candidates:
            if candidate in columns:
                return candidate

        return None

    def _count_starting_players(
        self,
        match_id: int,
        team_id: int,
    ) -> int:
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(
                    DISTINCT player_id
                )
            FROM lineups
            WHERE
                match_id = ?
                AND team_id = ?
                AND is_starting = 1
                AND player_id IS NOT NULL;
            """,
            (
                match_id,
                team_id,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return 0

        return int(
            row[0] or 0
        )

    @staticmethod
    def _validate_lineup(
        team_name: str,
        lineup_players: int,
    ) -> None:
        if lineup_players <= 0:
            raise ValueError(
                f"Für {team_name} ist keine "
                "Startelf vorhanden."
            )

    @staticmethod
    def _normalize_mode(
        mode: PredictionMode | str,
    ) -> PredictionMode:
        if isinstance(
            mode,
            PredictionMode,
        ):
            return mode

        normalized = (
            str(mode)
            .strip()
            .lower()
        )

        try:
            return PredictionMode(
                normalized
            )

        except ValueError as exc:
            raise ValueError(
                "Unbekannter Prediction-Modus. "
                "Erlaubt sind 'prematch' "
                "und 'lineup'."
            ) from exc