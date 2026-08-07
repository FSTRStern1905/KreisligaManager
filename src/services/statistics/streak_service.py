from __future__ import annotations

import sqlite3


class StreakService:
    """
    Berechnet Ergebnisserien innerhalb eines Wettbewerbs.

    Unterstützt:
    - längste Siegesserie
    - längste Unentschiedenserie
    - längste Niederlagenserie

    Die Berechnung erfolgt pro Mannschaft anhand aller
    abgeschlossenen Spiele in chronologischer Reihenfolge.
    """

    RESULT_WIN = "W"
    RESULT_DRAW = "D"
    RESULT_LOSS = "L"

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_team_streaks(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        teams = self._load_teams(
            competition_id
        )

        matches = self._load_matches(
            competition_id
        )

        results_by_team: dict[int, list[str]] = {
            team_id: []
            for team_id, _, _ in teams
        }

        for (
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
        ) in matches:
            home_result, away_result = (
                self._resolve_result(
                    home_goals=home_goals,
                    away_goals=away_goals,
                )
            )

            if home_team_id in results_by_team:
                results_by_team[
                    home_team_id
                ].append(
                    home_result
                )

            if away_team_id in results_by_team:
                results_by_team[
                    away_team_id
                ].append(
                    away_result
                )

        result: list[dict] = []

        for (
            team_id,
            team_name,
            short_name,
        ) in teams:
            team_results = results_by_team.get(
                team_id,
                [],
            )

            result.append(
                {
                    "team_id": team_id,
                    "team_name": (
                        short_name
                        or team_name
                    ),
                    "matches": len(
                        team_results
                    ),
                    "longest_win_streak": (
                        self._longest_streak(
                            team_results,
                            self.RESULT_WIN,
                        )
                    ),
                    "longest_draw_streak": (
                        self._longest_streak(
                            team_results,
                            self.RESULT_DRAW,
                        )
                    ),
                    "longest_loss_streak": (
                        self._longest_streak(
                            team_results,
                            self.RESULT_LOSS,
                        )
                    ),
                    "current_streak": (
                        self._current_streak(
                            team_results
                        )
                    ),
                }
            )

        return result

    def get_competition_records(
        self,
        competition_id: int,
    ) -> dict:
        team_streaks = self.get_team_streaks(
            competition_id
        )

        return {
            "win_streak": self._best_record(
                team_streaks,
                "longest_win_streak",
            ),
            "draw_streak": self._best_record(
                team_streaks,
                "longest_draw_streak",
            ),
            "loss_streak": self._best_record(
                team_streaks,
                "longest_loss_streak",
            ),
        }

    def _load_teams(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name,
                teams.short_name
            FROM competition_teams
            INNER JOIN teams
                ON teams.team_id =
                   competition_teams.team_id
            WHERE
                competition_teams.competition_id = ?
            ORDER BY
                teams.name;
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday ASC,
                match_date ASC,
                match_id ASC;
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    @classmethod
    def _resolve_result(
        cls,
        home_goals: int,
        away_goals: int,
    ) -> tuple[str, str]:
        if home_goals > away_goals:
            return (
                cls.RESULT_WIN,
                cls.RESULT_LOSS,
            )

        if home_goals < away_goals:
            return (
                cls.RESULT_LOSS,
                cls.RESULT_WIN,
            )

        return (
            cls.RESULT_DRAW,
            cls.RESULT_DRAW,
        )

    @staticmethod
    def _longest_streak(
        results: list[str],
        target: str,
    ) -> int:
        longest = 0
        current = 0

        for result in results:
            if result == target:
                current += 1
                longest = max(
                    longest,
                    current,
                )
            else:
                current = 0

        return longest

    @staticmethod
    def _current_streak(
        results: list[str],
    ) -> dict:
        if not results:
            return {
                "type": "",
                "length": 0,
            }

        streak_type = results[-1]
        length = 0

        for result in reversed(
            results
        ):
            if result != streak_type:
                break

            length += 1

        return {
            "type": streak_type,
            "length": length,
        }

    @staticmethod
    def _best_record(
        team_streaks: list[dict],
        key: str,
    ) -> dict | None:
        if not team_streaks:
            return None

        best = max(
            team_streaks,
            key=lambda row: int(
                row.get(
                    key,
                    0,
                )
            ),
        )

        return {
            "team_id": best[
                "team_id"
            ],
            "team_name": best[
                "team_name"
            ],
            "length": int(
                best.get(
                    key,
                    0,
                )
            ),
        }