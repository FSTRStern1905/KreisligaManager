from __future__ import annotations

import sqlite3

from src.services.statistics.player_statistics_service import (
    PlayerStatisticsService,
)


class PlayerRecordsService:
    MIN_MINUTES_FOR_RATE = 900
    MIN_APPEARANCES_FOR_RATE = 10

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

        self.player_statistics_service = (
            PlayerStatisticsService(
                connection
            )
        )

    def get_records(
        self,
        competition_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        statistics = (
            self.player_statistics_service
            .get_competition_statistics(
                competition_id=competition_id,
            )
        )

        active_players = [
            player
            for player in statistics
            if int(
                player.get(
                    "appearances",
                    0,
                )
            ) > 0
        ]

        match_records = (
            self._get_match_based_records(
                competition_id=competition_id,
                statistics=statistics,
            )
        )

        return {
            "most_goals": self._get_max_record(
                active_players,
                key="goals",
            ),
            "most_appearances": self._get_max_record(
                active_players,
                key="appearances",
            ),
            "most_starts": self._get_max_record(
                active_players,
                key="starts",
            ),
            "most_minutes": self._get_max_record(
                active_players,
                key="minutes_played",
            ),
            "most_substituted_in": self._get_max_record(
                active_players,
                key="substituted_in",
            ),
            "most_substituted_out": self._get_max_record(
                active_players,
                key="substituted_out",
            ),
            "most_yellow_cards": self._get_max_record(
                active_players,
                key="yellow_cards",
            ),
            "most_yellow_red_cards": self._get_max_record(
                active_players,
                key="yellow_red_cards",
            ),
            "most_red_cards": self._get_max_record(
                active_players,
                key="red_cards",
            ),
            "most_clean_sheets": self._get_max_record(
                active_players,
                key="clean_sheets",
            ),
            "best_goals_per_90": (
                self._get_best_goals_per_90(
                    active_players
                )
            ),
            "best_minutes_per_goal": (
                self._get_best_minutes_per_goal(
                    active_players
                )
            ),
            "best_goals_per_appearance": (
                self._get_best_goals_per_appearance(
                    active_players
                )
            ),
            "most_cards_per_90": (
                self._get_most_cards_per_90(
                    active_players
                )
            ),
            **match_records,
        }

    @staticmethod
    def _get_max_record(
        statistics: list[dict],
        key: str,
    ) -> dict | None:
        candidates = [
            player
            for player in statistics
            if int(
                player.get(
                    key,
                    0,
                )
            ) > 0
        ]

        if not candidates:
            return None

        player = max(
            candidates,
            key=lambda item: (
                int(
                    item.get(
                        key,
                        0,
                    )
                ),
                int(
                    item.get(
                        "minutes_played",
                        0,
                    )
                ),
                str(
                    item.get(
                        "player_name",
                        "",
                    )
                ).casefold(),
            ),
        )

        return PlayerRecordsService._create_record(
            player=player,
            value=int(
                player.get(
                    key,
                    0,
                )
            ),
        )

    def _get_best_goals_per_90(
        self,
        statistics: list[dict],
    ) -> dict | None:
        candidates = [
            player
            for player in statistics
            if (
                int(
                    player.get(
                        "minutes_played",
                        0,
                    )
                )
                >= self.MIN_MINUTES_FOR_RATE
                and int(
                    player.get(
                        "goals",
                        0,
                    )
                ) > 0
            )
        ]

        if not candidates:
            return None

        player = max(
            candidates,
            key=lambda item: (
                float(
                    item.get(
                        "goals_per_90",
                        0.0,
                    )
                ),
                int(
                    item.get(
                        "goals",
                        0,
                    )
                ),
                int(
                    item.get(
                        "minutes_played",
                        0,
                    )
                ),
            ),
        )

        record = self._create_record(
            player=player,
            value=round(
                float(
                    player.get(
                        "goals_per_90",
                        0.0,
                    )
                ),
                2,
            ),
        )

        record[
            "minimum_minutes"
        ] = self.MIN_MINUTES_FOR_RATE

        return record

    def _get_best_minutes_per_goal(
        self,
        statistics: list[dict],
    ) -> dict | None:
        candidates = [
            player
            for player in statistics
            if (
                int(
                    player.get(
                        "minutes_played",
                        0,
                    )
                )
                >= self.MIN_MINUTES_FOR_RATE
                and int(
                    player.get(
                        "goals",
                        0,
                    )
                ) > 0
                and player.get(
                    "minutes_per_goal"
                )
                is not None
            )
        ]

        if not candidates:
            return None

        player = min(
            candidates,
            key=lambda item: (
                float(
                    item[
                        "minutes_per_goal"
                    ]
                ),
                -int(
                    item.get(
                        "goals",
                        0,
                    )
                ),
                str(
                    item.get(
                        "player_name",
                        "",
                    )
                ).casefold(),
            ),
        )

        record = self._create_record(
            player=player,
            value=round(
                float(
                    player[
                        "minutes_per_goal"
                    ]
                ),
                1,
            ),
        )

        record[
            "minimum_minutes"
        ] = self.MIN_MINUTES_FOR_RATE

        return record

    @classmethod
    def _get_best_goals_per_appearance(
        cls,
        statistics: list[dict],
    ) -> dict | None:
        candidates = [
            player
            for player in statistics
            if (
                int(
                    player.get(
                        "appearances",
                        0,
                    )
                )
                >= cls.MIN_APPEARANCES_FOR_RATE
                and int(
                    player.get(
                        "goals",
                        0,
                    )
                ) > 0
            )
        ]

        if not candidates:
            return None

        def rate(
            player: dict,
        ) -> float:
            appearances = int(
                player.get(
                    "appearances",
                    0,
                )
            )

            goals = int(
                player.get(
                    "goals",
                    0,
                )
            )

            if appearances <= 0:
                return 0.0

            return (
                goals
                / appearances
            )

        player = max(
            candidates,
            key=lambda item: (
                rate(
                    item
                ),
                int(
                    item.get(
                        "goals",
                        0,
                    )
                ),
                int(
                    item.get(
                        "appearances",
                        0,
                    )
                ),
            ),
        )

        record = cls._create_record(
            player=player,
            value=round(
                rate(
                    player
                ),
                2,
            ),
        )

        record[
            "minimum_appearances"
        ] = cls.MIN_APPEARANCES_FOR_RATE

        return record

    def _get_most_cards_per_90(
        self,
        statistics: list[dict],
    ) -> dict | None:
        candidates = [
            player
            for player in statistics
            if (
                int(
                    player.get(
                        "minutes_played",
                        0,
                    )
                )
                >= self.MIN_MINUTES_FOR_RATE
                and (
                    int(
                        player.get(
                            "yellow_cards",
                            0,
                        )
                    )
                    + int(
                        player.get(
                            "yellow_red_cards",
                            0,
                        )
                    )
                    + int(
                        player.get(
                            "red_cards",
                            0,
                        )
                    )
                ) > 0
            )
        ]

        if not candidates:
            return None

        def rate(
            player: dict,
        ) -> float:
            cards = (
                int(
                    player.get(
                        "yellow_cards",
                        0,
                    )
                )
                + int(
                    player.get(
                        "yellow_red_cards",
                        0,
                    )
                )
                + int(
                    player.get(
                        "red_cards",
                        0,
                    )
                )
            )

            minutes = int(
                player.get(
                    "minutes_played",
                    0,
                )
            )

            if minutes <= 0:
                return 0.0

            return (
                cards
                * 90
                / minutes
            )

        player = max(
            candidates,
            key=lambda item: (
                rate(
                    item
                ),
                int(
                    item.get(
                        "yellow_cards",
                        0,
                    )
                )
                + int(
                    item.get(
                        "yellow_red_cards",
                        0,
                    )
                )
                + int(
                    item.get(
                        "red_cards",
                        0,
                    )
                ),
            ),
        )

        record = self._create_record(
            player=player,
            value=round(
                rate(
                    player
                ),
                2,
            ),
        )

        record[
            "minimum_minutes"
        ] = self.MIN_MINUTES_FOR_RATE

        return record

    def _get_match_based_records(
        self,
        competition_id: int,
        statistics: list[dict],
    ) -> dict:
        player_lookup = {
            int(
                player[
                    "player_id"
                ]
            ): player
            for player in statistics
        }

        self.cursor.execute(
            """
            SELECT
                player_match_stats.player_id,

                SUM(
                    CASE
                        WHEN player_match_stats.is_starting = 1
                        THEN player_match_stats.goals
                        ELSE 0
                    END
                ) AS starter_goals,

                SUM(
                    CASE
                        WHEN player_match_stats.was_substituted_in = 1
                        THEN player_match_stats.goals
                        ELSE 0
                    END
                ) AS substitute_goals,

                MAX(
                    player_match_stats.goals
                ) AS max_goals_in_match,

                SUM(
                    CASE
                        WHEN player_match_stats.goals >= 2
                        THEN 1
                        ELSE 0
                    END
                ) AS multi_goal_matches,

                SUM(
                    CASE
                        WHEN player_match_stats.goals >= 3
                        THEN 1
                        ELSE 0
                    END
                ) AS hattricks,

                SUM(
                    CASE
                        WHEN player_match_stats.goals > 0
                        THEN 1
                        ELSE 0
                    END
                ) AS scoring_matches

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            WHERE
                matches.competition_id = ?
                AND matches.status = 'finished'

            GROUP BY
                player_match_stats.player_id
            """,
            (
                competition_id,
            ),
        )

        rows: list[dict] = []

        for row in self.cursor.fetchall():
            player_id = int(
                row[0]
            )

            player = player_lookup.get(
                player_id
            )

            if player is None:
                continue

            rows.append(
                {
                    "player": player,
                    "starter_goals": int(
                        row[1]
                        or 0
                    ),
                    "substitute_goals": int(
                        row[2]
                        or 0
                    ),
                    "max_goals_in_match": int(
                        row[3]
                        or 0
                    ),
                    "multi_goal_matches": int(
                        row[4]
                        or 0
                    ),
                    "hattricks": int(
                        row[5]
                        or 0
                    ),
                    "scoring_matches": int(
                        row[6]
                        or 0
                    ),
                }
            )

        return {
            "most_starter_goals": (
                self._get_match_record(
                    rows,
                    key="starter_goals",
                )
            ),
            "most_substitute_goals": (
                self._get_match_record(
                    rows,
                    key="substitute_goals",
                )
            ),
            "most_goals_in_match": (
                self._get_match_record(
                    rows,
                    key="max_goals_in_match",
                )
            ),
            "most_multi_goal_matches": (
                self._get_match_record(
                    rows,
                    key="multi_goal_matches",
                )
            ),
            "most_hattricks": (
                self._get_match_record(
                    rows,
                    key="hattricks",
                )
            ),
            "most_scoring_matches": (
                self._get_match_record(
                    rows,
                    key="scoring_matches",
                )
            ),
        }

    @staticmethod
    def _get_match_record(
        rows: list[dict],
        key: str,
    ) -> dict | None:
        candidates = [
            row
            for row in rows
            if int(
                row.get(
                    key,
                    0,
                )
            ) > 0
        ]

        if not candidates:
            return None

        row = max(
            candidates,
            key=lambda item: (
                int(
                    item.get(
                        key,
                        0,
                    )
                ),
                int(
                    item[
                        "player"
                    ].get(
                        "goals",
                        0,
                    )
                ),
                int(
                    item[
                        "player"
                    ].get(
                        "minutes_played",
                        0,
                    )
                ),
            ),
        )

        return PlayerRecordsService._create_record(
            player=row[
                "player"
            ],
            value=int(
                row[
                    key
                ]
            ),
        )

    @staticmethod
    def _create_record(
        player: dict,
        value,
    ) -> dict:
        return {
            "player_id": int(
                player[
                    "player_id"
                ]
            ),
            "player_name": str(
                player[
                    "player_name"
                ]
            ),
            "team_id": int(
                player[
                    "team_id"
                ]
            ),
            "team_name": str(
                player[
                    "team_name"
                ]
            ),
            "appearances": int(
                player.get(
                    "appearances",
                    0,
                )
            ),
            "minutes_played": int(
                player.get(
                    "minutes_played",
                    0,
                )
            ),
            "goals": int(
                player.get(
                    "goals",
                    0,
                )
            ),
            "value": value,
        }