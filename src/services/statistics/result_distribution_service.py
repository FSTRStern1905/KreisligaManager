from __future__ import annotations

import sqlite3
from collections import Counter


class ResultDistributionService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_result_distribution(
        self,
        competition_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        matches = self._load_matches(
            competition_id
        )

        if not matches:
            return self._empty_result()

        total_matches = len(
            matches
        )

        home_wins = 0
        draws = 0
        away_wins = 0

        total_goals = 0

        over_2_5 = 0
        under_2_5 = 0

        both_teams_score = 0
        clean_sheet_matches = 0

        scorelines: Counter[str] = Counter()

        for (
            home_goals,
            away_goals,
        ) in matches:
            home_goals = int(
                home_goals
            )

            away_goals = int(
                away_goals
            )

            match_goals = (
                home_goals
                + away_goals
            )

            total_goals += (
                match_goals
            )

            if home_goals > away_goals:
                home_wins += 1

            elif home_goals < away_goals:
                away_wins += 1

            else:
                draws += 1

            if match_goals > 2:
                over_2_5 += 1

            else:
                under_2_5 += 1

            if (
                home_goals > 0
                and away_goals > 0
            ):
                both_teams_score += 1

            if (
                home_goals == 0
                or away_goals == 0
            ):
                clean_sheet_matches += 1

            scoreline = (
                f"{home_goals}:{away_goals}"
            )

            scorelines[
                scoreline
            ] += 1

        most_common_scorelines = [
            {
                "score": score,
                "count": count,
                "percentage": self._percentage(
                    count,
                    total_matches,
                ),
            }
            for score, count
            in scorelines.most_common(
                10
            )
        ]

        return {
            "total_matches": (
                total_matches
            ),
            "total_goals": (
                total_goals
            ),
            "average_goals": round(
                total_goals
                / total_matches,
                2,
            ),
            "home_wins": (
                home_wins
            ),
            "home_win_percentage": (
                self._percentage(
                    home_wins,
                    total_matches,
                )
            ),
            "draws": (
                draws
            ),
            "draw_percentage": (
                self._percentage(
                    draws,
                    total_matches,
                )
            ),
            "away_wins": (
                away_wins
            ),
            "away_win_percentage": (
                self._percentage(
                    away_wins,
                    total_matches,
                )
            ),
            "over_2_5": (
                over_2_5
            ),
            "over_2_5_percentage": (
                self._percentage(
                    over_2_5,
                    total_matches,
                )
            ),
            "under_2_5": (
                under_2_5
            ),
            "under_2_5_percentage": (
                self._percentage(
                    under_2_5,
                    total_matches,
                )
            ),
            "both_teams_score": (
                both_teams_score
            ),
            "both_teams_score_percentage": (
                self._percentage(
                    both_teams_score,
                    total_matches,
                )
            ),
            "clean_sheet_matches": (
                clean_sheet_matches
            ),
            "clean_sheet_percentage": (
                self._percentage(
                    clean_sheet_matches,
                    total_matches,
                )
            ),
            "most_common_scorelines": (
                most_common_scorelines
            ),
        }

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                matchday,
                match_id
            """,
            (
                competition_id,
            ),
        )

        return self.cursor.fetchall()

    @staticmethod
    def _percentage(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            value
            / total
            * 100,
            1,
        )

    @staticmethod
    def _empty_result(
    ) -> dict:
        return {
            "total_matches": 0,
            "total_goals": 0,
            "average_goals": 0.0,
            "home_wins": 0,
            "home_win_percentage": 0.0,
            "draws": 0,
            "draw_percentage": 0.0,
            "away_wins": 0,
            "away_win_percentage": 0.0,
            "over_2_5": 0,
            "over_2_5_percentage": 0.0,
            "under_2_5": 0,
            "under_2_5_percentage": 0.0,
            "both_teams_score": 0,
            "both_teams_score_percentage": 0.0,
            "clean_sheet_matches": 0,
            "clean_sheet_percentage": 0.0,
            "most_common_scorelines": [],
        }