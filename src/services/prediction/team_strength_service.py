from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
    HistoricalMatch,
)


@dataclass(frozen=True, slots=True)
class TeamStrength:
    team_id: int
    matches_played: int

    goals_for: int
    goals_against: int

    home_matches: int
    home_goals_for: int
    home_goals_against: int

    away_matches: int
    away_goals_for: int
    away_goals_against: int

    attack_strength: float
    defense_strength: float

    home_attack_strength: float
    home_defense_strength: float

    away_attack_strength: float
    away_defense_strength: float


@dataclass(frozen=True, slots=True)
class LeagueStrength:
    matches_played: int
    average_home_goals: float
    average_away_goals: float
    average_total_goals: float


class TeamStrengthService:
    """
    Prediction Engine v0.2

    Teamstärken werden bei kleinen Stichproben zum
    Ligadurchschnitt 1.0 geglättet.

    SMOOTHING_MATCHES = 5 bedeutet:
    - 1 echtes Spiel  -> 1/6 echter Wert, 5/6 Liga
    - 5 echte Spiele -> 1/2 echter Wert, 1/2 Liga
    - 10 Spiele      -> 2/3 echter Wert, 1/3 Liga

    Dadurch werden extreme Frühphasen-Werte reduziert.
    """

    SMOOTHING_MATCHES = 5.0

    def __init__(
        self,
        context: HistoricalDataContext,
    ) -> None:
        self.context = context
        self._matches = context.get_matches()
        self._league_strength = (
            self._calculate_league_strength()
        )

    def get_league_strength(self) -> LeagueStrength:
        return self._league_strength

    def get_team_strength(
        self,
        team_id: int,
    ) -> TeamStrength:
        matches = self.context.get_team_matches(
            team_id
        )

        home_matches = [
            match
            for match in matches
            if match.home_team_id == team_id
        ]
        away_matches = [
            match
            for match in matches
            if match.away_team_id == team_id
        ]

        goals_for = sum(
            self._goals_for(match, team_id)
            for match in matches
        )
        goals_against = sum(
            self._goals_against(match, team_id)
            for match in matches
        )

        home_goals_for = sum(
            match.home_goals
            for match in home_matches
        )
        home_goals_against = sum(
            match.away_goals
            for match in home_matches
        )

        away_goals_for = sum(
            match.away_goals
            for match in away_matches
        )
        away_goals_against = sum(
            match.home_goals
            for match in away_matches
        )

        league = self._league_strength

        league_overall_average = (
            league.average_total_goals / 2.0
        )

        attack_strength = self._smoothed_ratio(
            goals=goals_for,
            matches=len(matches),
            league_average=league_overall_average,
        )

        defense_strength = self._smoothed_ratio(
            goals=goals_against,
            matches=len(matches),
            league_average=league_overall_average,
        )

        home_attack_strength = self._smoothed_ratio(
            goals=home_goals_for,
            matches=len(home_matches),
            league_average=league.average_home_goals,
        )

        home_defense_strength = self._smoothed_ratio(
            goals=home_goals_against,
            matches=len(home_matches),
            league_average=league.average_away_goals,
        )

        away_attack_strength = self._smoothed_ratio(
            goals=away_goals_for,
            matches=len(away_matches),
            league_average=league.average_away_goals,
        )

        away_defense_strength = self._smoothed_ratio(
            goals=away_goals_against,
            matches=len(away_matches),
            league_average=league.average_home_goals,
        )

        return TeamStrength(
            team_id=team_id,
            matches_played=len(matches),
            goals_for=goals_for,
            goals_against=goals_against,
            home_matches=len(home_matches),
            home_goals_for=home_goals_for,
            home_goals_against=home_goals_against,
            away_matches=len(away_matches),
            away_goals_for=away_goals_for,
            away_goals_against=away_goals_against,
            attack_strength=attack_strength,
            defense_strength=defense_strength,
            home_attack_strength=home_attack_strength,
            home_defense_strength=home_defense_strength,
            away_attack_strength=away_attack_strength,
            away_defense_strength=away_defense_strength,
        )

    def _calculate_league_strength(
        self,
    ) -> LeagueStrength:
        matches_played = len(self._matches)

        if matches_played == 0:
            raise ValueError(
                "Keine historischen Ligaspiele vorhanden."
            )

        home_goals = sum(
            match.home_goals
            for match in self._matches
        )
        away_goals = sum(
            match.away_goals
            for match in self._matches
        )

        average_home_goals = (
            home_goals / matches_played
        )
        average_away_goals = (
            away_goals / matches_played
        )

        return LeagueStrength(
            matches_played=matches_played,
            average_home_goals=average_home_goals,
            average_away_goals=average_away_goals,
            average_total_goals=(
                average_home_goals
                + average_away_goals
            ),
        )

    def _smoothed_ratio(
        self,
        goals: int,
        matches: int,
        league_average: float,
    ) -> float:
        if league_average <= 0.0:
            return 1.0

        if matches <= 0:
            return 1.0

        raw_average = goals / matches
        raw_ratio = raw_average / league_average

        weight = (
            matches
            / (
                matches
                + self.SMOOTHING_MATCHES
            )
        )

        return (
            weight * raw_ratio
            + (1.0 - weight) * 1.0
        )

    @staticmethod
    def _goals_for(
        match: HistoricalMatch,
        team_id: int,
    ) -> int:
        if match.home_team_id == team_id:
            return match.home_goals

        return match.away_goals

    @staticmethod
    def _goals_against(
        match: HistoricalMatch,
        team_id: int,
    ) -> int:
        if match.home_team_id == team_id:
            return match.away_goals

        return match.home_goals
