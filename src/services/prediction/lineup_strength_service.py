from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.player_strength_service import (
    PlayerStrengthService,
)


@dataclass(frozen=True, slots=True)
class LineupPlayerStrength:
    player_id: int
    player_name: str
    overall_factor: float
    minutes_played: int
    starts: int


@dataclass(frozen=True, slots=True)
class LineupStrength:
    match_id: int
    team_id: int
    lineup_players: int
    known_players: int
    missing_players: int
    lineup_factor: float
    expected_lineup_factor: float
    relative_lineup_factor: float
    players: tuple[LineupPlayerStrength, ...]


class LineupStrengthService:
    EXPECTED_STARTERS = 11
    MIN_RELATIVE_FACTOR = 0.85
    MAX_RELATIVE_FACTOR = 1.15

    # Der rohe XI/Expected-XI-Quotient liegt empirisch sehr eng um 1.0.
    # Zentrum aus der ligaübergreifenden Diagnose (1388 Team-Lineups).
    # SCALE macht die Abweichung für das Modell sinnvoll nutzbar.
    RELATIVE_CENTER = 0.996689
    RELATIVE_SCALE = 10.0

    def __init__(
        self,
        context: HistoricalDataContext,
    ) -> None:
        self.context = context
        self.connection = context.connection
        self.player_strength_service = (
            PlayerStrengthService(context)
        )

        self._player_name_cache: dict[int, str] = {}
        self._expected_factor_cache: dict[int, float] = {}

    def get_lineup_strength(
        self,
        match_id: int,
        team_id: int,
    ) -> LineupStrength:
        """
        LINEUP mode only.

        Reads the actual starting XI of the target match, but evaluates
        every player exclusively from matches BEFORE the context cutoff.

        The target match result and target-match player statistics are
        never used here.
        """
        if match_id <= 0:
            raise ValueError("Ungültige Spiel-ID.")
        if team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")

        self._assert_target_match_allowed(
            match_id=match_id,
            team_id=team_id,
        )

        player_ids = self._get_starting_player_ids(
            match_id=match_id,
            team_id=team_id,
        )

        players: list[LineupPlayerStrength] = []

        for player_id in player_ids:
            try:
                strength = (
                    self.player_strength_service
                    .get_player_strength(
                        player_id=player_id,
                        team_id=team_id,
                    )
                )
            except ValueError:
                continue

            players.append(
                LineupPlayerStrength(
                    player_id=player_id,
                    player_name=self._get_player_name(
                        player_id
                    ),
                    overall_factor=strength.overall_factor,
                    minutes_played=strength.minutes_played,
                    starts=strength.starts,
                )
            )

        lineup_factor = self._weighted_lineup_factor(
            players
        )

        expected_lineup_factor = (
            self._get_expected_lineup_factor(team_id)
        )

        raw_relative_lineup_factor = self._safe_ratio(
            lineup_factor,
            expected_lineup_factor,
        )

        relative_lineup_factor = self._normalize_relative_factor(
            raw_relative_lineup_factor
        )

        return LineupStrength(
            match_id=match_id,
            team_id=team_id,
            lineup_players=len(player_ids),
            known_players=len(players),
            missing_players=max(
                self.EXPECTED_STARTERS - len(player_ids),
                0,
            ),
            lineup_factor=lineup_factor,
            expected_lineup_factor=expected_lineup_factor,
            relative_lineup_factor=relative_lineup_factor,
            players=tuple(players),
        )

    def _get_expected_lineup_factor(
        self,
        team_id: int,
    ) -> float:
        if team_id in self._expected_factor_cache:
            return self._expected_factor_cache[team_id]

        strengths = list(
            self.player_strength_service
            .get_team_player_strengths(team_id)
        )

        if not strengths:
            self._expected_factor_cache[team_id] = 1.0
            return 1.0

        # Erwartete Startelf = die historisch am häufigsten
        # eingesetzten Starter. Die Spielerstärke entscheidet nur
        # bei gleicher Start-/Einsatzhistorie und erzeugt damit
        # keine künstliche "Best-of-XI".
        strengths.sort(
            key=lambda player: (
                player.starts,
                player.matches_played,
                player.minutes_played,
                player.overall_factor,
            ),
            reverse=True,
        )

        expected_starters = strengths[
            : self.EXPECTED_STARTERS
        ]

        if not expected_starters:
            result = 1.0
        else:
            # Gleiche Berechnung wie bei der tatsächlichen Startelf:
            # historische Minuten gewichten den Faktor.
            total_weight = 0.0
            weighted_sum = 0.0

            for player in expected_starters:
                weight = max(
                    float(player.minutes_played),
                    90.0,
                )
                total_weight += weight
                weighted_sum += (
                    player.overall_factor * weight
                )

            result = (
                weighted_sum / total_weight
                if total_weight > 0.0
                else 1.0
            )

        self._expected_factor_cache[team_id] = result
        return result

    def _get_starting_player_ids(
        self,
        match_id: int,
        team_id: int,
    ) -> tuple[int, ...]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT DISTINCT
                lineups.player_id
            FROM lineups
            WHERE
                lineups.match_id = ?
                AND lineups.team_id = ?
                AND lineups.is_starting = 1
                AND lineups.player_id IS NOT NULL
            ORDER BY lineups.lineup_id;
            """,
            (
                match_id,
                team_id,
            ),
        )

        return tuple(
            int(row[0])
            for row in cursor.fetchall()
        )

    def _assert_target_match_allowed(
        self,
        match_id: int,
        team_id: int,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                competition_id,
                matchday,
                home_team_id,
                away_team_id
            FROM matches
            WHERE match_id = ?;
            """,
            (match_id,),
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Spiel-ID {match_id} wurde nicht gefunden."
            )

        competition_id = int(row[0])
        matchday = row[1]
        home_team_id = int(row[2])
        away_team_id = int(row[3])

        if competition_id != self.context.competition_id:
            raise ValueError(
                "Das Spiel gehört nicht zum Wettbewerb "
                "des HistoricalDataContext."
            )

        if matchday is None:
            raise ValueError(
                "Das Zielspiel besitzt keinen Spieltag."
            )

        if int(matchday) != self.context.cutoff_matchday:
            raise ValueError(
                "LINEUP Prediction erwartet als Zielspiel "
                "genau den Cutoff-Spieltag."
            )

        if team_id not in (
            home_team_id,
            away_team_id,
        ):
            raise ValueError(
                "Die Mannschaft gehört nicht zum Zielspiel."
            )

    @staticmethod
    def _weighted_lineup_factor(
        players: list[LineupPlayerStrength],
    ) -> float:
        if not players:
            return 1.0

        total_weight = 0.0
        weighted_sum = 0.0

        for player in players:
            weight = max(
                float(player.minutes_played),
                90.0,
            )
            total_weight += weight
            weighted_sum += (
                player.overall_factor * weight
            )

        if total_weight <= 0.0:
            return 1.0

        return weighted_sum / total_weight

    def _get_player_name(
        self,
        player_id: int,
    ) -> str:
        if player_id in self._player_name_cache:
            return self._player_name_cache[player_id]

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                first_name,
                last_name
            FROM players
            WHERE player_id = ?;
            """,
            (player_id,),
        )

        row = cursor.fetchone()

        if row is None:
            name = f"Spieler {player_id}"
        else:
            first_name = (
                str(row[0]).strip()
                if row[0]
                else ""
            )
            last_name = (
                str(row[1]).strip()
                if row[1]
                else ""
            )

            name = " ".join(
                part
                for part in (
                    first_name,
                    last_name,
                )
                if part
            )

            if not name:
                name = f"Spieler {player_id}"

        self._player_name_cache[player_id] = name
        return name

    def _normalize_relative_factor(
        self,
        raw_factor: float,
    ) -> float:
        centered_deviation = (
            raw_factor - self.RELATIVE_CENTER
        )

        normalized_factor = (
            1.0
            + centered_deviation
            * self.RELATIVE_SCALE
        )

        return self._clamp(
            normalized_factor,
            self.MIN_RELATIVE_FACTOR,
            self.MAX_RELATIVE_FACTOR,
        )

    @staticmethod
    def _safe_ratio(
        numerator: float,
        denominator: float,
    ) -> float:
        if denominator <= 0.0:
            return 1.0

        return numerator / denominator

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        return max(
            minimum,
            min(value, maximum),
        )
