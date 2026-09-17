from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)


@dataclass(frozen=True, slots=True)
class PlayerStrength:
    player_id: int
    team_id: int
    matches_played: int
    starts: int
    minutes_played: int
    goals: int
    assists: int
    yellow_cards: int
    yellow_red_cards: int
    red_cards: int
    minutes_per_match: float
    goals_per_90: float
    assists_per_90: float
    goal_contributions_per_90: float
    start_rate: float
    availability_factor: float
    attacking_factor: float
    experience_factor: float
    overall_factor: float


@dataclass(frozen=True, slots=True)
class TeamPlayerStrength:
    team_id: int
    historical_players: int
    core_players: int
    total_minutes: int
    core_minutes: int
    core_minutes_share: float
    weighted_player_strength: float
    top_player_strength: float
    squad_stability: float
    team_player_factor: float
    league_average_player_factor: float
    relative_team_player_factor: float


class PlayerStrengthService:
    MINUTES_PER_MATCH = 90.0

    AVAILABILITY_SMOOTHING = 3.0
    ATTACKING_SMOOTHING_MINUTES = 450.0
    EXPERIENCE_SMOOTHING_MINUTES = 450.0

    MAX_AVAILABILITY_FACTOR = 1.20
    MAX_ATTACKING_FACTOR = 1.50
    MAX_EXPERIENCE_FACTOR = 1.20
    MAX_OVERALL_FACTOR = 1.35

    def __init__(
        self,
        context: HistoricalDataContext,
    ) -> None:
        self.context = context
        self.connection = context.connection

        self._player_strength_cache: dict[
            tuple[int, int],
            PlayerStrength,
        ] = {}
        self._team_strengths_cache: dict[
            int,
            tuple[PlayerStrength, ...],
        ] = {}
        self._raw_team_factor_cache: dict[
            tuple[int, int],
            float | None,
        ] = {}
        self._league_average_cache: dict[int, float] = {}

    def get_player_strength(
        self,
        player_id: int,
        team_id: int | None = None,
    ) -> PlayerStrength:
        if player_id <= 0:
            raise ValueError("Ungültige Spieler-ID.")

        if team_id is None:
            team_id = self._get_historical_team_id(
                player_id
            )

        if team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")

        cache_key = (player_id, team_id)

        if cache_key in self._player_strength_cache:
            return self._player_strength_cache[cache_key]

        stats = self._get_historical_stats(
            player_id=player_id,
            team_id=team_id,
        )

        matches_played = int(stats["matches_played"])
        starts = int(stats["starts"])
        minutes_played = int(stats["minutes_played"])
        goals = int(stats["goals"])
        assists = int(stats["assists"])
        yellow_cards = int(stats["yellow_cards"])
        yellow_red_cards = int(stats["yellow_red_cards"])
        red_cards = int(stats["red_cards"])

        minutes_per_match = self._safe_divide(
            minutes_played,
            matches_played,
        )
        goals_per_90 = self._per_90(
            goals,
            minutes_played,
        )
        assists_per_90 = self._per_90(
            assists,
            minutes_played,
        )
        goal_contributions_per_90 = self._per_90(
            goals + assists,
            minutes_played,
        )
        start_rate = self._safe_divide(
            starts,
            matches_played,
        )

        availability_factor = self._availability_factor(
            matches_played=matches_played,
            starts=starts,
        )
        attacking_factor = self._attacking_factor(
            goals=goals,
            assists=assists,
            minutes_played=minutes_played,
        )
        experience_factor = self._experience_factor(
            minutes_played=minutes_played,
        )

        overall_factor = self._overall_factor(
            availability_factor=availability_factor,
            attacking_factor=attacking_factor,
            experience_factor=experience_factor,
        )

        result = PlayerStrength(
            player_id=player_id,
            team_id=team_id,
            matches_played=matches_played,
            starts=starts,
            minutes_played=minutes_played,
            goals=goals,
            assists=assists,
            yellow_cards=yellow_cards,
            yellow_red_cards=yellow_red_cards,
            red_cards=red_cards,
            minutes_per_match=minutes_per_match,
            goals_per_90=goals_per_90,
            assists_per_90=assists_per_90,
            goal_contributions_per_90=(
                goal_contributions_per_90
            ),
            start_rate=start_rate,
            availability_factor=availability_factor,
            attacking_factor=attacking_factor,
            experience_factor=experience_factor,
            overall_factor=overall_factor,
        )

        self._player_strength_cache[cache_key] = result
        return result

    def get_team_player_strengths(
        self,
        team_id: int,
    ) -> tuple[PlayerStrength, ...]:
        if team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")

        if team_id in self._team_strengths_cache:
            return self._team_strengths_cache[team_id]

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT DISTINCT
                players.player_id
            FROM players
            INNER JOIN player_match_stats
                ON player_match_stats.player_id = players.player_id
            INNER JOIN matches
                ON matches.match_id = player_match_stats.match_id
            WHERE
                player_match_stats.team_id = ?
                AND matches.competition_id = ?
                AND matches.matchday IS NOT NULL
                AND matches.matchday < ?
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL
            ORDER BY players.player_id;
            """,
            (
                team_id,
                self.context.competition_id,
                self.context.cutoff_matchday,
            ),
        )

        result = tuple(
            self.get_player_strength(
                player_id=int(row[0]),
                team_id=team_id,
            )
            for row in cursor.fetchall()
        )

        self._team_strengths_cache[team_id] = result
        return result

    def get_team_player_strength(
        self,
        team_id: int,
        core_size: int = 14,
    ) -> TeamPlayerStrength:
        if team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")
        if core_size <= 0:
            raise ValueError(
                "core_size muss größer als 0 sein."
            )

        strengths = list(
            self.get_team_player_strengths(team_id)
        )

        if not strengths:
            return TeamPlayerStrength(
                team_id=team_id,
                historical_players=0,
                core_players=0,
                total_minutes=0,
                core_minutes=0,
                core_minutes_share=0.0,
                weighted_player_strength=1.0,
                top_player_strength=1.0,
                squad_stability=1.0,
                team_player_factor=1.0,
                league_average_player_factor=1.0,
                relative_team_player_factor=1.0,
            )

        strengths.sort(
            key=lambda player: (
                player.minutes_played,
                player.starts,
                player.overall_factor,
            ),
            reverse=True,
        )

        core = strengths[:core_size]

        total_minutes = sum(
            player.minutes_played
            for player in strengths
        )
        core_minutes = sum(
            player.minutes_played
            for player in core
        )

        core_minutes_share = self._safe_divide(
            core_minutes,
            total_minutes,
        )

        weighted_player_strength = (
            self._minutes_weighted_strength(core)
        )

        top_players = sorted(
            core,
            key=lambda player: player.overall_factor,
            reverse=True,
        )[:5]

        top_player_strength = (
            sum(
                player.overall_factor
                for player in top_players
            )
            / len(top_players)
            if top_players
            else 1.0
        )

        squad_stability = self._squad_stability(
            core=core,
            core_minutes_share=core_minutes_share,
        )

        team_player_factor = (
            weighted_player_strength * 0.60
            + top_player_strength * 0.20
            + squad_stability * 0.20
        )

        team_player_factor = self._clamp(
            team_player_factor,
            0.90,
            1.20,
        )

        league_average_player_factor = (
            self._get_league_average_player_factor(
                core_size=core_size,
            )
        )

        relative_team_player_factor = self._safe_divide(
            team_player_factor,
            league_average_player_factor,
        )

        if relative_team_player_factor <= 0.0:
            relative_team_player_factor = 1.0

        return TeamPlayerStrength(
            team_id=team_id,
            historical_players=len(strengths),
            core_players=len(core),
            total_minutes=total_minutes,
            core_minutes=core_minutes,
            core_minutes_share=core_minutes_share,
            weighted_player_strength=(
                weighted_player_strength
            ),
            top_player_strength=top_player_strength,
            squad_stability=squad_stability,
            team_player_factor=team_player_factor,
            league_average_player_factor=(
                league_average_player_factor
            ),
            relative_team_player_factor=(
                relative_team_player_factor
            ),
        )

    def get_relative_team_player_factor(
        self,
        team_id: int,
        core_size: int = 14,
    ) -> float:
        return self.get_team_player_strength(
            team_id=team_id,
            core_size=core_size,
        ).relative_team_player_factor

    def _get_league_average_player_factor(
        self,
        core_size: int,
    ) -> float:
        if core_size in self._league_average_cache:
            return self._league_average_cache[core_size]

        team_ids = self._get_historical_team_ids()

        raw_factors = []

        for team_id in team_ids:
            raw_factor = self._get_raw_team_player_factor(
                team_id=team_id,
                core_size=core_size,
            )
            if raw_factor is not None:
                raw_factors.append(raw_factor)

        if not raw_factors:
            result = 1.0
        else:
            result = sum(raw_factors) / len(raw_factors)

        self._league_average_cache[core_size] = result
        return result

    def _get_raw_team_player_factor(
        self,
        team_id: int,
        core_size: int,
    ) -> float | None:
        cache_key = (team_id, core_size)

        if cache_key in self._raw_team_factor_cache:
            return self._raw_team_factor_cache[cache_key]

        strengths = list(
            self.get_team_player_strengths(team_id)
        )

        if not strengths:
            self._raw_team_factor_cache[cache_key] = None
            return None

        strengths.sort(
            key=lambda player: (
                player.minutes_played,
                player.starts,
                player.overall_factor,
            ),
            reverse=True,
        )

        core = strengths[:core_size]

        total_minutes = sum(
            player.minutes_played
            for player in strengths
        )
        core_minutes = sum(
            player.minutes_played
            for player in core
        )

        core_minutes_share = self._safe_divide(
            core_minutes,
            total_minutes,
        )

        weighted_player_strength = (
            self._minutes_weighted_strength(core)
        )

        top_players = sorted(
            core,
            key=lambda player: player.overall_factor,
            reverse=True,
        )[:5]

        top_player_strength = (
            sum(
                player.overall_factor
                for player in top_players
            )
            / len(top_players)
            if top_players
            else 1.0
        )

        squad_stability = self._squad_stability(
            core=core,
            core_minutes_share=core_minutes_share,
        )

        factor = (
            weighted_player_strength * 0.60
            + top_player_strength * 0.20
            + squad_stability * 0.20
        )

        return self._clamp(
            factor,
            0.90,
            1.20,
        )

    def _get_historical_team_ids(
        self,
    ) -> tuple[int, ...]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT DISTINCT
                player_match_stats.team_id
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id = player_match_stats.match_id
            WHERE
                matches.competition_id = ?
                AND matches.matchday IS NOT NULL
                AND matches.matchday < ?
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL
            ORDER BY player_match_stats.team_id;
            """,
            (
                self.context.competition_id,
                self.context.cutoff_matchday,
            ),
        )

        return tuple(
            int(row[0])
            for row in cursor.fetchall()
        )

    def _minutes_weighted_strength(
        self,
        players: list[PlayerStrength],
    ) -> float:
        total_minutes = sum(
            player.minutes_played
            for player in players
        )

        if total_minutes <= 0:
            return 1.0

        return sum(
            player.overall_factor
            * player.minutes_played
            for player in players
        ) / total_minutes

    def _squad_stability(
        self,
        core: list[PlayerStrength],
        core_minutes_share: float,
    ) -> float:
        if not core:
            return 1.0

        average_start_rate = sum(
            player.start_rate
            for player in core
        ) / len(core)

        raw_factor = (
            0.90
            + 0.10 * core_minutes_share
            + 0.10 * average_start_rate
        )

        return self._clamp(
            raw_factor,
            0.90,
            1.10,
        )

    def _get_historical_team_id(
        self,
        player_id: int,
    ) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                player_match_stats.team_id
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id = player_match_stats.match_id
            WHERE
                player_match_stats.player_id = ?
                AND matches.competition_id = ?
                AND matches.matchday IS NOT NULL
                AND matches.matchday < ?
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL
            ORDER BY
                matches.matchday DESC,
                matches.match_id DESC
            LIMIT 1;
            """,
            (
                player_id,
                self.context.competition_id,
                self.context.cutoff_matchday,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Für Spieler-ID {player_id} wurden vor "
                f"Spieltag {self.context.cutoff_matchday} "
                "keine historischen Einsätze gefunden."
            )

        return int(row[0])

    def _get_historical_stats(
        self,
        player_id: int,
        team_id: int,
    ):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT player_match_stats.match_id)
                    AS matches_played,
                COALESCE(
                    SUM(player_match_stats.is_starting),
                    0
                ) AS starts,
                COALESCE(
                    SUM(player_match_stats.minutes_played),
                    0
                ) AS minutes_played,
                COALESCE(
                    SUM(player_match_stats.goals),
                    0
                ) AS goals,
                COALESCE(
                    SUM(player_match_stats.assists),
                    0
                ) AS assists,
                COALESCE(
                    SUM(player_match_stats.yellow_cards),
                    0
                ) AS yellow_cards,
                COALESCE(
                    SUM(player_match_stats.yellow_red_cards),
                    0
                ) AS yellow_red_cards,
                COALESCE(
                    SUM(player_match_stats.red_cards),
                    0
                ) AS red_cards
            FROM player_match_stats
            INNER JOIN matches
                ON matches.match_id = player_match_stats.match_id
            WHERE
                player_match_stats.player_id = ?
                AND player_match_stats.team_id = ?
                AND matches.competition_id = ?
                AND matches.matchday IS NOT NULL
                AND matches.matchday < ?
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL;
            """,
            (
                player_id,
                team_id,
                self.context.competition_id,
                self.context.cutoff_matchday,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return {
                "matches_played": 0,
                "starts": 0,
                "minutes_played": 0,
                "goals": 0,
                "assists": 0,
                "yellow_cards": 0,
                "yellow_red_cards": 0,
                "red_cards": 0,
            }

        return {
            "matches_played": row[0],
            "starts": row[1],
            "minutes_played": row[2],
            "goals": row[3],
            "assists": row[4],
            "yellow_cards": row[5],
            "yellow_red_cards": row[6],
            "red_cards": row[7],
        }

    @staticmethod
    def _safe_divide(
        numerator: float,
        denominator: float,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return numerator / denominator

    @classmethod
    def _per_90(
        cls,
        value: float,
        minutes_played: int,
    ) -> float:
        if minutes_played <= 0:
            return 0.0

        return (
            value
            * cls.MINUTES_PER_MATCH
            / minutes_played
        )

    def _availability_factor(
        self,
        matches_played: int,
        starts: int,
    ) -> float:
        if matches_played <= 0:
            return 1.0

        start_rate = starts / matches_played

        raw_factor = 0.85 + (0.30 * start_rate)

        weight = matches_played / (
            matches_played
            + self.AVAILABILITY_SMOOTHING
        )

        factor = (
            weight * raw_factor
            + (1.0 - weight) * 1.0
        )

        return self._clamp(
            factor,
            0.85,
            self.MAX_AVAILABILITY_FACTOR,
        )

    def _attacking_factor(
        self,
        goals: int,
        assists: int,
        minutes_played: int,
    ) -> float:
        if minutes_played <= 0:
            return 1.0

        contributions_per_90 = self._per_90(
            goals + assists,
            minutes_played,
        )

        raw_factor = 1.0 + (
            contributions_per_90 * 0.35
        )

        weight = minutes_played / (
            minutes_played
            + self.ATTACKING_SMOOTHING_MINUTES
        )

        factor = (
            weight * raw_factor
            + (1.0 - weight) * 1.0
        )

        return self._clamp(
            factor,
            1.0,
            self.MAX_ATTACKING_FACTOR,
        )

    def _experience_factor(
        self,
        minutes_played: int,
    ) -> float:
        if minutes_played <= 0:
            return 1.0

        raw_factor = 1.0 + min(
            minutes_played / 2700.0,
            1.0,
        ) * 0.15

        weight = minutes_played / (
            minutes_played
            + self.EXPERIENCE_SMOOTHING_MINUTES
        )

        factor = (
            weight * raw_factor
            + (1.0 - weight) * 1.0
        )

        return self._clamp(
            factor,
            1.0,
            self.MAX_EXPERIENCE_FACTOR,
        )

    def _overall_factor(
        self,
        availability_factor: float,
        attacking_factor: float,
        experience_factor: float,
    ) -> float:
        factor = (
            availability_factor * 0.25
            + attacking_factor * 0.50
            + experience_factor * 0.25
        )

        return self._clamp(
            factor,
            0.85,
            self.MAX_OVERALL_FACTOR,
        )

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
