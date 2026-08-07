from __future__ import annotations

import sqlite3
from collections.abc import Iterable


class SeasonComparisonService:
    GOAL_EVENT_CODES = (
        "GOAL",
        "PENALTY_GOAL",
    )

    CARD_EVENT_CODES = (
        "YELLOW_CARD",
        "YELLOW_RED_CARD",
        "RED_CARD",
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_team_seasons(
        self,
        team_id: int,
    ) -> list[dict]:
        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        self.cursor.execute(
            """
            SELECT DISTINCT
                seasons.season_id,
                seasons.name,
                competitions.competition_id,
                competitions.name
            FROM matches
            INNER JOIN seasons
                ON seasons.season_id =
                    matches.season_id
            LEFT JOIN competitions
                ON competitions.competition_id =
                    matches.competition_id
            WHERE
                matches.home_team_id = ?
                OR matches.away_team_id = ?
            ORDER BY
                seasons.start_date ASC,
                seasons.season_id ASC,
                competitions.name COLLATE NOCASE ASC;
            """,
            (
                team_id,
                team_id,
            ),
        )

        return [
            {
                "season_id": int(row[0]),
                "season_name": row[1] or (
                    f"Saison {row[0]}"
                ),
                "competition_id": (
                    int(row[2])
                    if row[2] is not None
                    else None
                ),
                "competition_name": (
                    row[3]
                    or "Ohne Wettbewerb"
                ),
            }
            for row in self.cursor.fetchall()
        ]

    def compare(
        self,
        team_id: int,
        competition_ids: Iterable[int],
    ) -> list[dict]:
        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        normalized_ids = []

        for competition_id in competition_ids:
            competition_id = int(
                competition_id
            )

            if competition_id <= 0:
                continue

            if competition_id not in normalized_ids:
                normalized_ids.append(
                    competition_id
                )

        if not normalized_ids:
            return []

        return [
            self.get_competition_statistics(
                team_id=team_id,
                competition_id=competition_id,
            )
            for competition_id in normalized_ids
        ]

    def get_competition_statistics(
        self,
        team_id: int,
        competition_id: int,
    ) -> dict:
        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        metadata = self._load_metadata(
            team_id,
            competition_id,
        )

        matches = self._load_finished_matches(
            team_id,
            competition_id,
        )

        stats = {
            **metadata,
            "matches": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
            "points_per_match": 0.0,
            "goals_per_match": 0.0,
            "goals_against_per_match": 0.0,
            "longest_win_streak": 0,
            "longest_draw_streak": 0,
            "longest_loss_streak": 0,
            "yellow_cards": 0,
            "yellow_red_cards": 0,
            "red_cards": 0,
            "different_scorers": 0,
        }

        outcomes: list[str] = []

        for match in matches:
            (
                _match_id,
                home_team_id,
                away_team_id,
                home_goals,
                away_goals,
            ) = match

            if home_team_id == team_id:
                goals_for = home_goals
                goals_against = away_goals
            elif away_team_id == team_id:
                goals_for = away_goals
                goals_against = home_goals
            else:
                continue

            stats["matches"] += 1
            stats["goals_for"] += goals_for
            stats["goals_against"] += goals_against

            if goals_for > goals_against:
                stats["wins"] += 1
                stats["points"] += 3
                outcomes.append(
                    "W"
                )

            elif goals_for < goals_against:
                stats["losses"] += 1
                outcomes.append(
                    "L"
                )

            else:
                stats["draws"] += 1
                stats["points"] += 1
                outcomes.append(
                    "D"
                )

        stats["goal_difference"] = (
            stats["goals_for"]
            - stats["goals_against"]
        )

        if stats["matches"] > 0:
            stats["points_per_match"] = round(
                stats["points"]
                / stats["matches"],
                2,
            )

            stats["goals_per_match"] = round(
                stats["goals_for"]
                / stats["matches"],
                2,
            )

            stats["goals_against_per_match"] = round(
                stats["goals_against"]
                / stats["matches"],
                2,
            )

        stats["longest_win_streak"] = (
            self._longest_streak(
                outcomes,
                "W",
            )
        )

        stats["longest_draw_streak"] = (
            self._longest_streak(
                outcomes,
                "D",
            )
        )

        stats["longest_loss_streak"] = (
            self._longest_streak(
                outcomes,
                "L",
            )
        )

        card_stats = self._load_card_stats(
            team_id,
            competition_id,
        )

        stats.update(
            card_stats
        )

        stats["different_scorers"] = (
            self._load_scorer_count(
                team_id,
                competition_id,
            )
        )

        return stats

    def _load_metadata(
        self,
        team_id: int,
        competition_id: int,
    ) -> dict:
        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name,
                teams.short_name,
                competitions.competition_id,
                competitions.name,
                seasons.season_id,
                seasons.name
            FROM teams
            INNER JOIN competitions
                ON competitions.competition_id = ?
            INNER JOIN seasons
                ON seasons.season_id =
                    competitions.season_id
            WHERE
                teams.team_id = ?
            LIMIT 1;
            """,
            (
                competition_id,
                team_id,
            ),
        )

        row = self.cursor.fetchone()

        if row is None:
            raise ValueError(
                "Mannschaft oder Wettbewerb "
                "wurde nicht gefunden."
            )

        return {
            "team_id": int(row[0]),
            "team_name": (
                row[2]
                or row[1]
                or f"Mannschaft {row[0]}"
            ),
            "competition_id": int(row[3]),
            "competition_name": (
                row[4]
                or f"Wettbewerb {row[3]}"
            ),
            "season_id": int(row[5]),
            "season_name": (
                row[6]
                or f"Saison {row[5]}"
            ),
        }

    def _load_finished_matches(
        self,
        team_id: int,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                match_id,
                home_team_id,
                away_team_id,
                home_goals,
                away_goals
            FROM matches
            WHERE
                competition_id = ?
                AND (
                    home_team_id = ?
                    OR away_team_id = ?
                )
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            ORDER BY
                CASE
                    WHEN match_date IS NULL THEN 1
                    ELSE 0
                END,
                match_date ASC,
                kickoff_time ASC,
                matchday ASC,
                match_id ASC;
            """,
            (
                competition_id,
                team_id,
                team_id,
            ),
        )

        return self.cursor.fetchall()

    def _load_card_stats(
        self,
        team_id: int,
        competition_id: int,
    ) -> dict:
        result = {
            "yellow_cards": 0,
            "yellow_red_cards": 0,
            "red_cards": 0,
        }

        self.cursor.execute(
            """
            SELECT
                event_types.code,
                COUNT(events.event_id)
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                    events.event_type_id
            INNER JOIN matches
                ON matches.match_id =
                    events.match_id
            WHERE
                matches.competition_id = ?
                AND events.team_id = ?
                AND event_types.code IN (
                    'YELLOW_CARD',
                    'YELLOW_RED_CARD',
                    'RED_CARD'
                )
            GROUP BY
                event_types.code;
            """,
            (
                competition_id,
                team_id,
            ),
        )

        for event_code, count in self.cursor.fetchall():
            if event_code == "YELLOW_CARD":
                result["yellow_cards"] = int(
                    count
                )

            elif event_code == "YELLOW_RED_CARD":
                result["yellow_red_cards"] = int(
                    count
                )

            elif event_code == "RED_CARD":
                result["red_cards"] = int(
                    count
                )

        return result

    def _load_scorer_count(
        self,
        team_id: int,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT
                COUNT(
                    DISTINCT events.player_id
                )
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                    events.event_type_id
            INNER JOIN matches
                ON matches.match_id =
                    events.match_id
            WHERE
                matches.competition_id = ?
                AND events.team_id = ?
                AND events.player_id IS NOT NULL
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL'
                );
            """,
            (
                competition_id,
                team_id,
            ),
        )

        result = self.cursor.fetchone()

        if result is None:
            return 0

        return int(
            result[0] or 0
        )

    @staticmethod
    def _longest_streak(
        outcomes: Iterable[str],
        target: str,
    ) -> int:
        longest = 0
        current = 0

        for outcome in outcomes:
            if outcome == target:
                current += 1
                longest = max(
                    longest,
                    current,
                )
            else:
                current = 0

        return longest