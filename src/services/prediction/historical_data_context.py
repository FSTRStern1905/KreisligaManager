from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HistoricalMatch:
    match_id: int
    competition_id: int
    matchday: int
    home_team_id: int
    away_team_id: int
    home_goals: int
    away_goals: int


class HistoricalDataContext:
    """Provides only matches completed before a prediction cutoff.

    The cutoff matchday itself and all later matchdays are intentionally
    inaccessible through this context.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        competition_id: int,
        cutoff_matchday: int,
    ) -> None:
        if competition_id <= 0:
            raise ValueError("Ungültige Wettbewerb-ID.")

        if cutoff_matchday <= 0:
            raise ValueError("Ungültiger Prognose-Stichtag.")

        self.connection = connection
        self.competition_id = competition_id
        self.cutoff_matchday = cutoff_matchday

    def get_matches(self) -> list[HistoricalMatch]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                match_id,
                competition_id,
                matchday,
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND matchday IS NOT NULL
                AND matchday < ?
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday,
                match_id;
            """,
            (
                self.competition_id,
                self.cutoff_matchday,
            ),
        )

        return [
            HistoricalMatch(
                match_id=int(row[0]),
                competition_id=int(row[1]),
                matchday=int(row[2]),
                home_team_id=int(row[3]),
                away_team_id=int(row[4]),
                home_goals=int(row[5]),
                away_goals=int(row[6]),
            )
            for row in cursor.fetchall()
        ]

    def get_team_matches(
        self,
        team_id: int,
    ) -> list[HistoricalMatch]:
        if team_id <= 0:
            raise ValueError("Ungültige Mannschaft-ID.")

        return [
            match
            for match in self.get_matches()
            if (
                match.home_team_id == team_id
                or match.away_team_id == team_id
            )
        ]

    def get_matches_before_matchday(
        self,
        matchday: int,
    ) -> list[HistoricalMatch]:
        if matchday > self.cutoff_matchday:
            raise ValueError(
                "Zugriff auf zukünftige Spieltage ist gesperrt."
            )

        if matchday <= 0:
            raise ValueError("Ungültiger Spieltag.")

        return [
            match
            for match in self.get_matches()
            if match.matchday < matchday
        ]

    def assert_matchday_allowed(
        self,
        matchday: int,
    ) -> None:
        if matchday >= self.cutoff_matchday:
            raise PermissionError(
                "Prediction-Datenleck verhindert: "
                f"Spieltag {matchday} liegt am oder nach dem "
                f"Stichtag {self.cutoff_matchday}."
            )
