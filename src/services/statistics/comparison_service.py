from __future__ import annotations

import sqlite3

from src.services.statistics.form_service import (
    FormService,
)
from src.services.statistics.table_service import (
    TableService,
)


class ComparisonService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.table_service = TableService(
            connection
        )

        self.form_service = FormService(
            connection
        )

    def get_team_comparison(
        self,
        competition_id: int,
        team_a_id: int,
        team_b_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if team_a_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID A."
            )

        if team_b_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID B."
            )

        if team_a_id == team_b_id:
            raise ValueError(
                "Bitte zwei unterschiedliche "
                "Mannschaften auswählen."
            )

        overall_table = (
            self.table_service.get_table(
                competition_id=competition_id,
                mode="all",
            )
        )

        home_table = (
            self.table_service.get_table(
                competition_id=competition_id,
                mode="home",
            )
        )

        away_table = (
            self.table_service.get_table(
                competition_id=competition_id,
                mode="away",
            )
        )

        form_table = (
            self.form_service.get_form_table(
                competition_id=competition_id,
                matches=5,
            )
        )

        team_a = self._build_team_data(
            team_id=team_a_id,
            overall_table=overall_table,
            home_table=home_table,
            away_table=away_table,
            form_table=form_table,
        )

        team_b = self._build_team_data(
            team_id=team_b_id,
            overall_table=overall_table,
            home_table=home_table,
            away_table=away_table,
            form_table=form_table,
        )

        if team_a is None:
            raise ValueError(
                "Mannschaft A wurde im Wettbewerb "
                "nicht gefunden."
            )

        if team_b is None:
            raise ValueError(
                "Mannschaft B wurde im Wettbewerb "
                "nicht gefunden."
            )

        head_to_head = (
            self.get_head_to_head(
                competition_id=competition_id,
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                team_a_name=team_a["team_name"],
                team_b_name=team_b["team_name"],
            )
        )

        return {
            "team_a": team_a,
            "team_b": team_b,
            "head_to_head": head_to_head,
        }

    def get_teams(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        table = self.table_service.get_table(
            competition_id=competition_id,
            mode="all",
        )

        return [
            {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "position": index + 1,
            }
            for index, team in enumerate(
                table
            )
        ]

    def get_head_to_head(
        self,
        competition_id: int,
        team_a_id: int,
        team_b_id: int,
        team_a_name: str,
        team_b_name: str,
    ) -> dict:
        self.cursor.execute(
            """
            SELECT
                match_id,
                matchday,
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
                AND (
                    (
                        home_team_id = ?
                        AND away_team_id = ?
                    )
                    OR
                    (
                        home_team_id = ?
                        AND away_team_id = ?
                    )
                )
            ORDER BY
                matchday DESC,
                match_id DESC
            """,
            (
                competition_id,
                team_a_id,
                team_b_id,
                team_b_id,
                team_a_id,
            ),
        )

        rows = self.cursor.fetchall()

        team_a_wins = 0
        team_b_wins = 0
        draws = 0

        team_a_goals = 0
        team_b_goals = 0

        matches: list[dict] = []

        for row in rows:
            (
                match_id,
                matchday,
                home_team_id,
                away_team_id,
                home_goals,
                away_goals,
            ) = row

            home_goals = int(
                home_goals
            )

            away_goals = int(
                away_goals
            )

            home_is_team_a = (
                int(home_team_id)
                == team_a_id
            )

            if home_is_team_a:
                home_name = team_a_name
                away_name = team_b_name

                team_a_match_goals = (
                    home_goals
                )

                team_b_match_goals = (
                    away_goals
                )

            else:
                home_name = team_b_name
                away_name = team_a_name

                team_a_match_goals = (
                    away_goals
                )

                team_b_match_goals = (
                    home_goals
                )

            team_a_goals += (
                team_a_match_goals
            )

            team_b_goals += (
                team_b_match_goals
            )

            if (
                team_a_match_goals
                > team_b_match_goals
            ):
                team_a_wins += 1

                result_for_team_a = (
                    "S"
                )

            elif (
                team_a_match_goals
                < team_b_match_goals
            ):
                team_b_wins += 1

                result_for_team_a = (
                    "N"
                )

            else:
                draws += 1

                result_for_team_a = (
                    "U"
                )

            matches.append(
                {
                    "match_id": int(
                        match_id
                    ),
                    "matchday": (
                        int(matchday)
                        if matchday is not None
                        else None
                    ),
                    "home_team_id": int(
                        home_team_id
                    ),
                    "away_team_id": int(
                        away_team_id
                    ),
                    "home_team_name": (
                        home_name
                    ),
                    "away_team_name": (
                        away_name
                    ),
                    "home_goals": (
                        home_goals
                    ),
                    "away_goals": (
                        away_goals
                    ),
                    "team_a_goals": (
                        team_a_match_goals
                    ),
                    "team_b_goals": (
                        team_b_match_goals
                    ),
                    "team_a_result": (
                        result_for_team_a
                    ),
                }
            )

        return {
            "matches_played": len(
                rows
            ),
            "team_a_wins": (
                team_a_wins
            ),
            "draws": draws,
            "team_b_wins": (
                team_b_wins
            ),
            "team_a_goals": (
                team_a_goals
            ),
            "team_b_goals": (
                team_b_goals
            ),
            "goal_difference": (
                team_a_goals
                - team_b_goals
            ),
            "matches": matches,
        }

    def _build_team_data(
        self,
        team_id: int,
        overall_table: list[dict],
        home_table: list[dict],
        away_table: list[dict],
        form_table: list[dict],
    ) -> dict | None:
        overall = self._find_team(
            overall_table,
            team_id,
        )

        if overall is None:
            return None

        home = self._find_team(
            home_table,
            team_id,
        )

        away = self._find_team(
            away_table,
            team_id,
        )

        form = self._find_team(
            form_table,
            team_id,
        )

        if home is None:
            home = self._empty_team_data(
                overall
            )

        if away is None:
            away = self._empty_team_data(
                overall
            )

        position = self._find_position(
            overall_table,
            team_id,
        )

        home_position = self._find_position(
            home_table,
            team_id,
        )

        away_position = self._find_position(
            away_table,
            team_id,
        )

        points_per_game = self._safe_ratio(
            overall["points"],
            overall["played"],
        )

        goals_per_game = self._safe_ratio(
            overall["goals_for"],
            overall["played"],
        )

        goals_against_per_game = (
            self._safe_ratio(
                overall["goals_against"],
                overall["played"],
            )
        )

        home_points_per_game = (
            self._safe_ratio(
                home["points"],
                home["played"],
            )
        )

        away_points_per_game = (
            self._safe_ratio(
                away["points"],
                away["played"],
            )
        )

        return {
            "team_id": overall[
                "team_id"
            ],
            "team_name": overall[
                "team_name"
            ],

            "position": position,

            "played": overall[
                "played"
            ],
            "wins": overall[
                "wins"
            ],
            "draws": overall[
                "draws"
            ],
            "losses": overall[
                "losses"
            ],

            "goals_for": overall[
                "goals_for"
            ],
            "goals_against": overall[
                "goals_against"
            ],
            "goal_difference": overall[
                "goal_difference"
            ],

            "points": overall[
                "points"
            ],

            "points_per_game": round(
                points_per_game,
                2,
            ),

            "goals_per_game": round(
                goals_per_game,
                2,
            ),

            "goals_against_per_game": round(
                goals_against_per_game,
                2,
            ),

            "home_position": (
                home_position
            ),
            "home_played": home[
                "played"
            ],
            "home_wins": home[
                "wins"
            ],
            "home_draws": home[
                "draws"
            ],
            "home_losses": home[
                "losses"
            ],
            "home_goals_for": home[
                "goals_for"
            ],
            "home_goals_against": home[
                "goals_against"
            ],
            "home_goal_difference": home[
                "goal_difference"
            ],
            "home_points": home[
                "points"
            ],
            "home_points_per_game": round(
                home_points_per_game,
                2,
            ),

            "away_position": (
                away_position
            ),
            "away_played": away[
                "played"
            ],
            "away_wins": away[
                "wins"
            ],
            "away_draws": away[
                "draws"
            ],
            "away_losses": away[
                "losses"
            ],
            "away_goals_for": away[
                "goals_for"
            ],
            "away_goals_against": away[
                "goals_against"
            ],
            "away_goal_difference": away[
                "goal_difference"
            ],
            "away_points": away[
                "points"
            ],
            "away_points_per_game": round(
                away_points_per_game,
                2,
            ),

            "form": (
                form.get(
                    "form",
                    [],
                )
                if form is not None
                else []
            ),

            "form_text": (
                form.get(
                    "form_text",
                    "",
                )
                if form is not None
                else ""
            ),
        }

    @staticmethod
    def _empty_team_data(
        team: dict,
    ) -> dict:
        return {
            "team_id": team[
                "team_id"
            ],
            "team_name": team[
                "team_name"
            ],
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        }

    @staticmethod
    def _find_team(
        table: list[dict],
        team_id: int,
    ) -> dict | None:
        for team in table:
            if (
                int(
                    team["team_id"]
                )
                == team_id
            ):
                return team

        return None

    @staticmethod
    def _find_position(
        table: list[dict],
        team_id: int,
    ) -> int | None:
        for index, team in enumerate(
            table,
            start=1,
        ):
            if (
                int(
                    team["team_id"]
                )
                == team_id
            ):
                return index

        return None

    @staticmethod
    def _safe_ratio(
        value: int | float,
        divisor: int | float,
    ) -> float:
        if divisor == 0:
            return 0.0

        return (
            float(value)
            / float(divisor)
        )