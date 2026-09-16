from __future__ import annotations

from dataclasses import dataclass

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
    HistoricalMatch,
)


@dataclass(frozen=True, slots=True)
class TeamForm:
    team_id: int
    matches_used: int
    goals_for: int
    goals_against: int
    points: int
    points_per_game: float
    goal_difference_per_game: float
    attack_factor: float
    defense_factor: float


class FormService:
    """
    Berechnet ausschließlich die letzten bereits bekannten Spiele
    aus dem HistoricalDataContext.

    Dadurch bleibt der Stichtag-Schutz vollständig erhalten.
    """

    DEFAULT_MATCHES = 5
    SMOOTHING_MATCHES = 3.0
    OLDEST_WEIGHT = 0.10

    def __init__(
        self,
        context: HistoricalDataContext,
    ) -> None:
        self.context = context

    def get_team_form(
        self,
        team_id: int,
        last_matches: int = DEFAULT_MATCHES,
    ) -> TeamForm:
        if last_matches <= 0:
            raise ValueError(
                "last_matches muss größer als 0 sein."
            )

        matches = self.context.get_team_matches(
            team_id
        )

        matches = sorted(
            matches,
            key=lambda match: (
                match.matchday,
                match.match_id,
            ),
        )[-last_matches:]

        if not matches:
            return TeamForm(
                team_id=team_id,
                matches_used=0,
                goals_for=0,
                goals_against=0,
                points=0,
                points_per_game=0.0,
                goal_difference_per_game=0.0,
                attack_factor=1.0,
                defense_factor=1.0,
            )

        goals_for = 0
        goals_against = 0
        points = 0

        weighted_goals_for = 0.0
        weighted_goals_against = 0.0
        total_weight = 0.0

        matches_used = len(matches)

        for index, match in enumerate(matches):
            scored = self._goals_for(
                match,
                team_id,
            )
            conceded = self._goals_against(
                match,
                team_id,
            )

            goals_for += scored
            goals_against += conceded

            if scored > conceded:
                points += 3
            elif scored == conceded:
                points += 1

            weight = self._recency_weight(
                index=index,
                matches_used=matches_used,
            )

            weighted_goals_for += scored * weight
            weighted_goals_against += conceded * weight
            total_weight += weight

        points_per_game = points / matches_used

        goal_difference_per_game = (
            goals_for - goals_against
        ) / matches_used

        league_matches = self.context.get_matches()

        if not league_matches:
            league_goals_per_team = 1.0
        else:
            total_goals = sum(
                match.home_goals
                + match.away_goals
                for match in league_matches
            )
            league_goals_per_team = (
                total_goals
                / (len(league_matches) * 2)
            )

        weighted_goals_for_per_match = (
            weighted_goals_for / total_weight
        )
        weighted_goals_against_per_match = (
            weighted_goals_against / total_weight
        )

        attack_factor = self._smoothed_factor(
            value_per_match=(
                weighted_goals_for_per_match
            ),
            league_average=league_goals_per_team,
            matches_used=matches_used,
        )

        defense_factor = self._smoothed_factor(
            value_per_match=(
                weighted_goals_against_per_match
            ),
            league_average=league_goals_per_team,
            matches_used=matches_used,
        )

        return TeamForm(
            team_id=team_id,
            matches_used=matches_used,
            goals_for=goals_for,
            goals_against=goals_against,
            points=points,
            points_per_game=points_per_game,
            goal_difference_per_game=(
                goal_difference_per_game
            ),
            attack_factor=attack_factor,
            defense_factor=defense_factor,
        )

    @staticmethod
    def _recency_weight(
        index: int,
        matches_used: int,
    ) -> float:
        if matches_used <= 1:
            return 1.0

        oldest_weight = FormService.OLDEST_WEIGHT
        newest_weight = 1.0

        progress = index / (matches_used - 1)

        return (
            oldest_weight
            + progress
            * (newest_weight - oldest_weight)
        )

    def _smoothed_factor(
        self,
        value_per_match: float,
        league_average: float,
        matches_used: int,
    ) -> float:
        if league_average <= 0.0:
            return 1.0

        raw_factor = (
            value_per_match
            / league_average
        )

        weight = (
            matches_used
            / (
                matches_used
                + self.SMOOTHING_MATCHES
            )
        )

        return (
            weight * raw_factor
            + (1.0 - weight)
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
