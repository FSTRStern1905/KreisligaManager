from __future__ import annotations

import sqlite3

from src.services.statistics.records_service import (
    RecordsService,
)


class CompetitionOverviewService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.records_service = RecordsService(
            connection
        )

    def get_overview(
        self,
        competition_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        competition = self._load_competition(
            competition_id
        )

        if competition is None:
            raise ValueError(
                "Wettbewerb wurde nicht gefunden."
            )

        match_stats = self._load_match_stats(
            competition_id
        )

        event_stats = self._load_event_stats(
            competition_id
        )

        records = (
            self.records_service.get_records(
                competition_id
            )
        )

        finished_matches = (
            match_stats["finished_matches"]
        )

        goals = match_stats["goals"]

        goals_per_match = (
            round(
                goals / finished_matches,
                2,
            )
            if finished_matches > 0
            else 0.0
        )

        detail_import_rate = (
            round(
                (
                    match_stats[
                        "detail_imported_matches"
                    ]
                    / finished_matches
                )
                * 100,
                2,
            )
            if finished_matches > 0
            else 0.0
        )

        home_win_rate = self._calculate_rate(
            match_stats["home_wins"],
            finished_matches,
        )

        draw_rate = self._calculate_rate(
            match_stats["draws"],
            finished_matches,
        )

        away_win_rate = self._calculate_rate(
            match_stats["away_wins"],
            finished_matches,
        )

        total_cards = (
            event_stats["yellow_cards"]
            + event_stats["yellow_red_cards"]
            + event_stats["red_cards"]
        )

        return {
            "competition_id": competition_id,
            "competition_name": (
                competition["competition_name"]
            ),
            "league_id": competition["league_id"],
            "league_name": competition["league_name"],
            "season_id": competition["season_id"],
            "season_name": competition["season_name"],
            "active": bool(
                competition["active"]
            ),
            "team_count": (
                competition["team_count"]
            ),
            "matches_total": (
                match_stats["matches_total"]
            ),
            "finished_matches": finished_matches,
            "scheduled_matches": (
                match_stats["scheduled_matches"]
            ),
            "unfinished_matches": (
                match_stats["unfinished_matches"]
            ),
            "detail_imported_matches": (
                match_stats[
                    "detail_imported_matches"
                ]
            ),
            "detail_import_rate": (
                detail_import_rate
            ),
            "current_matchday": (
                match_stats["current_matchday"]
            ),
            "maximum_matchday": (
                match_stats["maximum_matchday"]
            ),
            "goals": goals,
            "home_goals": (
                match_stats["home_goals"]
            ),
            "away_goals": (
                match_stats["away_goals"]
            ),
            "goals_per_match": goals_per_match,
            "home_wins": (
                match_stats["home_wins"]
            ),
            "draws": (
                match_stats["draws"]
            ),
            "away_wins": (
                match_stats["away_wins"]
            ),
            "home_win_rate": home_win_rate,
            "draw_rate": draw_rate,
            "away_win_rate": away_win_rate,
            "different_scorers": (
                event_stats["different_scorers"]
            ),
            "yellow_cards": (
                event_stats["yellow_cards"]
            ),
            "yellow_red_cards": (
                event_stats["yellow_red_cards"]
            ),
            "red_cards": (
                event_stats["red_cards"]
            ),
            "cards_total": total_cards,
            "records": records,
        }

    def get_competitions(
        self,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                competitions.competition_id,
                competitions.name,
                competitions.active,
                leagues.name AS league_name,
                seasons.name AS season_name

            FROM competitions

            LEFT JOIN leagues
                ON leagues.league_id =
                   competitions.league_id

            INNER JOIN seasons
                ON seasons.season_id =
                   competitions.season_id

            ORDER BY
                seasons.start_date DESC,
                competitions.name ASC
            """
        )

        result = []

        for row in self.cursor.fetchall():
            result.append(
                {
                    "competition_id": int(
                        row[0]
                    ),
                    "competition_name": (
                        row[1]
                    ),
                    "active": bool(
                        row[2]
                    ),
                    "league_name": (
                        row[3]
                    ),
                    "season_name": (
                        row[4]
                    ),
                }
            )

        return result

    def _load_competition(
        self,
        competition_id: int,
    ) -> dict | None:
        self.cursor.execute(
            """
            SELECT
                competitions.name,
                competitions.league_id,
                leagues.name,
                competitions.season_id,
                seasons.name,
                competitions.active,
                COUNT(
                    DISTINCT
                    competition_teams.team_id
                ) AS team_count

            FROM competitions

            LEFT JOIN leagues
                ON leagues.league_id =
                   competitions.league_id

            INNER JOIN seasons
                ON seasons.season_id =
                   competitions.season_id

            LEFT JOIN competition_teams
                ON competition_teams.competition_id =
                   competitions.competition_id

            WHERE
                competitions.competition_id = ?

            GROUP BY
                competitions.competition_id,
                competitions.name,
                competitions.league_id,
                leagues.name,
                competitions.season_id,
                seasons.name,
                competitions.active
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return {
            "competition_name": row[0],
            "league_id": row[1],
            "league_name": row[2],
            "season_id": row[3],
            "season_name": row[4],
            "active": row[5],
            "team_count": int(
                row[6] or 0
            ),
        }

    def _load_match_stats(
        self,
        competition_id: int,
    ) -> dict:
        self.cursor.execute(
            """
            SELECT
                COUNT(*) AS matches_total,

                SUM(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS finished_matches,

                SUM(
                    CASE
                        WHEN status = 'scheduled'
                        THEN 1
                        ELSE 0
                    END
                ) AS scheduled_matches,

                SUM(
                    CASE
                        WHEN
                            NOT (
                                status = 'finished'
                                AND home_goals
                                    IS NOT NULL
                                AND away_goals
                                    IS NOT NULL
                            )
                            AND status != 'scheduled'
                        THEN 1
                        ELSE 0
                    END
                ) AS unfinished_matches,

                SUM(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                        THEN home_goals
                        ELSE 0
                    END
                ) AS home_goals,

                SUM(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                        THEN away_goals
                        ELSE 0
                    END
                ) AS away_goals,

                SUM(
                    CASE
                        WHEN detail_imported = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS detail_imported_matches,

                MAX(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                        THEN matchday
                        ELSE NULL
                    END
                ) AS current_matchday,

                MAX(matchday)
                    AS maximum_matchday,

                SUM(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                            AND home_goals > away_goals
                        THEN 1
                        ELSE 0
                    END
                ) AS home_wins,

                SUM(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                            AND home_goals = away_goals
                        THEN 1
                        ELSE 0
                    END
                ) AS draws,

                SUM(
                    CASE
                        WHEN
                            status = 'finished'
                            AND home_goals
                                IS NOT NULL
                            AND away_goals
                                IS NOT NULL
                            AND home_goals < away_goals
                        THEN 1
                        ELSE 0
                    END
                ) AS away_wins

            FROM matches

            WHERE
                competition_id = ?
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return self._empty_match_stats()

        home_goals = int(
            row[4] or 0
        )

        away_goals = int(
            row[5] or 0
        )

        return {
            "matches_total": int(
                row[0] or 0
            ),
            "finished_matches": int(
                row[1] or 0
            ),
            "scheduled_matches": int(
                row[2] or 0
            ),
            "unfinished_matches": int(
                row[3] or 0
            ),
            "home_goals": home_goals,
            "away_goals": away_goals,
            "goals": (
                home_goals
                + away_goals
            ),
            "detail_imported_matches": int(
                row[6] or 0
            ),
            "current_matchday": (
                int(row[7])
                if row[7] is not None
                else None
            ),
            "maximum_matchday": (
                int(row[8])
                if row[8] is not None
                else None
            ),
            "home_wins": int(
                row[9] or 0
            ),
            "draws": int(
                row[10] or 0
            ),
            "away_wins": int(
                row[11] or 0
            ),
        }

    def _load_event_stats(
        self,
        competition_id: int,
    ) -> dict:
        self.cursor.execute(
            """
            SELECT
                COUNT(
                    DISTINCT
                    CASE
                        WHEN
                            event_types.code IN (
                                'GOAL',
                                'PENALTY_GOAL'
                            )
                            AND events.player_id
                                IS NOT NULL
                        THEN events.player_id
                    END
                ) AS different_scorers,

                SUM(
                    CASE
                        WHEN
                            event_types.code =
                            'YELLOW_CARD'
                        THEN 1
                        ELSE 0
                    END
                ) AS yellow_cards,

                SUM(
                    CASE
                        WHEN
                            event_types.code =
                            'YELLOW_RED_CARD'
                        THEN 1
                        ELSE 0
                    END
                ) AS yellow_red_cards,

                SUM(
                    CASE
                        WHEN
                            event_types.code =
                            'RED_CARD'
                        THEN 1
                        ELSE 0
                    END
                ) AS red_cards

            FROM events

            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id

            INNER JOIN matches
                ON matches.match_id =
                   events.match_id

            WHERE
                matches.competition_id = ?
            """,
            (competition_id,),
        )

        row = self.cursor.fetchone()

        if row is None:
            return self._empty_event_stats()

        return {
            "different_scorers": int(
                row[0] or 0
            ),
            "yellow_cards": int(
                row[1] or 0
            ),
            "yellow_red_cards": int(
                row[2] or 0
            ),
            "red_cards": int(
                row[3] or 0
            ),
        }

    @staticmethod
    def _calculate_rate(
        value: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            (
                value
                / total
            )
            * 100,
            2,
        )

    @staticmethod
    def _empty_match_stats(
    ) -> dict:
        return {
            "matches_total": 0,
            "finished_matches": 0,
            "scheduled_matches": 0,
            "unfinished_matches": 0,
            "home_goals": 0,
            "away_goals": 0,
            "goals": 0,
            "detail_imported_matches": 0,
            "current_matchday": None,
            "maximum_matchday": None,
            "home_wins": 0,
            "draws": 0,
            "away_wins": 0,
        }

    @staticmethod
    def _empty_event_stats(
    ) -> dict:
        return {
            "different_scorers": 0,
            "yellow_cards": 0,
            "yellow_red_cards": 0,
            "red_cards": 0,
        }