from __future__ import annotations

import sqlite3


class RecordsService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_records(
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

        team_statistics = (
            self._build_team_statistics(
                competition_id=competition_id,
                matches=matches,
            )
        )

        streak_records = (
            self._build_streak_records(
                competition_id=competition_id,
                matches=matches,
            )
        )

        return {
            "biggest_home_win": (
                self._get_biggest_home_win(
                    matches
                )
            ),
            "biggest_away_win": (
                self._get_biggest_away_win(
                    matches
                )
            ),
            "biggest_win": (
                self._get_biggest_win(
                    matches
                )
            ),
            "highest_scoring_match": (
                self._get_highest_scoring_match(
                    matches
                )
            ),
            "most_home_goals_match": (
                self._get_most_home_goals_match(
                    matches
                )
            ),
            "most_away_goals_match": (
                self._get_most_away_goals_match(
                    matches
                )
            ),
            "highest_scoring_draw": (
                self._get_highest_scoring_draw(
                    matches
                )
            ),
            "best_offense": (
                self._get_team_record(
                    team_statistics,
                    key="goals_for",
                    highest=True,
                )
            ),
            "best_defense": (
                self._get_team_record(
                    team_statistics,
                    key="goals_against",
                    highest=False,
                )
            ),
            "worst_offense": (
                self._get_team_record(
                    team_statistics,
                    key="goals_for",
                    highest=False,
                )
            ),
            "worst_defense": (
                self._get_team_record(
                    team_statistics,
                    key="goals_against",
                    highest=True,
                )
            ),
            "most_wins": (
                self._get_team_record(
                    team_statistics,
                    key="wins",
                    highest=True,
                )
            ),
            "most_draws": (
                self._get_team_record(
                    team_statistics,
                    key="draws",
                    highest=True,
                )
            ),
            "most_losses": (
                self._get_team_record(
                    team_statistics,
                    key="losses",
                    highest=True,
                )
            ),
            "best_goal_difference": (
                self._get_team_record(
                    team_statistics,
                    key="goal_difference",
                    highest=True,
                )
            ),
            "worst_goal_difference": (
                self._get_team_record(
                    team_statistics,
                    key="goal_difference",
                    highest=False,
                )
            ),
            "longest_win_streak": (
                streak_records[
                    "longest_win_streak"
                ]
            ),
            "longest_unbeaten_streak": (
                streak_records[
                    "longest_unbeaten_streak"
                ]
            ),
            "longest_loss_streak": (
                streak_records[
                    "longest_loss_streak"
                ]
            ),
            "longest_winless_streak": (
                streak_records[
                    "longest_winless_streak"
                ]
            ),
            "longest_scoring_streak": (
                streak_records[
                    "longest_scoring_streak"
                ]
            ),
            "longest_clean_sheet_streak": (
                streak_records[
                    "longest_clean_sheet_streak"
                ]
            ),
        }

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[dict]:
        self.cursor.execute(
            """
            SELECT
                matches.match_id,
                matches.matchday,
                matches.match_date,
                matches.home_team_id,
                home_teams.name,
                home_teams.short_name,
                matches.away_team_id,
                away_teams.name,
                away_teams.short_name,
                matches.home_goals,
                matches.away_goals

            FROM matches

            INNER JOIN teams AS home_teams
                ON home_teams.team_id =
                   matches.home_team_id

            INNER JOIN teams AS away_teams
                ON away_teams.team_id =
                   matches.away_team_id

            WHERE
                matches.competition_id = ?
                AND matches.status = 'finished'
                AND matches.home_goals IS NOT NULL
                AND matches.away_goals IS NOT NULL

            ORDER BY
                matches.matchday ASC,
                matches.match_date ASC,
                matches.match_id ASC
            """,
            (competition_id,),
        )

        result: list[dict] = []

        for row in self.cursor.fetchall():
            result.append(
                {
                    "match_id": int(
                        row[0]
                    ),
                    "matchday": row[1],
                    "match_date": row[2],
                    "home_team_id": int(
                        row[3]
                    ),
                    "home_team_name": (
                        row[5]
                        or row[4]
                    ),
                    "away_team_id": int(
                        row[6]
                    ),
                    "away_team_name": (
                        row[8]
                        or row[7]
                    ),
                    "home_goals": int(
                        row[9]
                    ),
                    "away_goals": int(
                        row[10]
                    ),
                }
            )

        return result

    def _load_competition_teams(
        self,
        competition_id: int,
    ) -> dict[int, str]:
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
                teams.name ASC
            """,
            (competition_id,),
        )

        teams: dict[int, str] = {}

        for (
            team_id,
            team_name,
            short_name,
        ) in self.cursor.fetchall():
            teams[int(team_id)] = (
                short_name
                or team_name
            )

        return teams

    def _build_team_statistics(
        self,
        competition_id: int,
        matches: list[dict],
    ) -> list[dict]:
        teams = self._load_competition_teams(
            competition_id
        )

        statistics: dict[int, dict] = {}

        for (
            team_id,
            team_name,
        ) in teams.items():
            statistics[team_id] = {
                "team_id": team_id,
                "team_name": team_name,
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
            }

        for match in matches:
            home = statistics.get(
                match["home_team_id"]
            )

            away = statistics.get(
                match["away_team_id"]
            )

            if home is None or away is None:
                continue

            home_goals = match[
                "home_goals"
            ]

            away_goals = match[
                "away_goals"
            ]

            home["played"] += 1
            away["played"] += 1

            home["goals_for"] += (
                home_goals
            )

            home["goals_against"] += (
                away_goals
            )

            away["goals_for"] += (
                away_goals
            )

            away["goals_against"] += (
                home_goals
            )

            if home_goals > away_goals:
                home["wins"] += 1
                away["losses"] += 1

            elif home_goals < away_goals:
                away["wins"] += 1
                home["losses"] += 1

            else:
                home["draws"] += 1
                away["draws"] += 1

        for row in statistics.values():
            row["goal_difference"] = (
                row["goals_for"]
                - row["goals_against"]
            )

        return list(
            statistics.values()
        )

    def _build_streak_records(
        self,
        competition_id: int,
        matches: list[dict],
    ) -> dict:
        teams = self._load_competition_teams(
            competition_id
        )

        histories: dict[
            int,
            list[dict],
        ] = {
            team_id: []
            for team_id in teams
        }

        for match in matches:
            home_team_id = (
                match["home_team_id"]
            )

            away_team_id = (
                match["away_team_id"]
            )

            home_goals = (
                match["home_goals"]
            )

            away_goals = (
                match["away_goals"]
            )

            if home_goals > away_goals:
                home_result = "W"
                away_result = "L"

            elif home_goals < away_goals:
                home_result = "L"
                away_result = "W"

            else:
                home_result = "D"
                away_result = "D"

            if home_team_id in histories:
                histories[
                    home_team_id
                ].append(
                    {
                        "match_id": (
                            match["match_id"]
                        ),
                        "matchday": (
                            match["matchday"]
                        ),
                        "match_date": (
                            match["match_date"]
                        ),
                        "result": home_result,
                        "goals_for": (
                            home_goals
                        ),
                        "goals_against": (
                            away_goals
                        ),
                    }
                )

            if away_team_id in histories:
                histories[
                    away_team_id
                ].append(
                    {
                        "match_id": (
                            match["match_id"]
                        ),
                        "matchday": (
                            match["matchday"]
                        ),
                        "match_date": (
                            match["match_date"]
                        ),
                        "result": away_result,
                        "goals_for": (
                            away_goals
                        ),
                        "goals_against": (
                            home_goals
                        ),
                    }
                )

        record_definitions = {
            "longest_win_streak": (
                lambda item:
                    item["result"] == "W"
            ),
            "longest_unbeaten_streak": (
                lambda item:
                    item["result"] != "L"
            ),
            "longest_loss_streak": (
                lambda item:
                    item["result"] == "L"
            ),
            "longest_winless_streak": (
                lambda item:
                    item["result"] != "W"
            ),
            "longest_scoring_streak": (
                lambda item:
                    item["goals_for"] > 0
            ),
            "longest_clean_sheet_streak": (
                lambda item:
                    item["goals_against"] == 0
            ),
        }

        records: dict[
            str,
            dict | None,
        ] = {
            key: None
            for key in record_definitions
        }

        for (
            team_id,
            history,
        ) in histories.items():
            team_name = teams[
                team_id
            ]

            for (
                record_key,
                condition,
            ) in record_definitions.items():
                streak = (
                    self._calculate_longest_streak(
                        history=history,
                        condition=condition,
                    )
                )

                if streak is None:
                    continue

                candidate = {
                    "team_id": team_id,
                    "team_name": team_name,
                    "length": streak[
                        "length"
                    ],
                    "start_match_id": (
                        streak[
                            "start_match_id"
                        ]
                    ),
                    "end_match_id": (
                        streak[
                            "end_match_id"
                        ]
                    ),
                    "start_matchday": (
                        streak[
                            "start_matchday"
                        ]
                    ),
                    "end_matchday": (
                        streak[
                            "end_matchday"
                        ]
                    ),
                    "start_date": (
                        streak[
                            "start_date"
                        ]
                    ),
                    "end_date": (
                        streak[
                            "end_date"
                        ]
                    ),
                }

                current = records[
                    record_key
                ]

                if (
                    current is None
                    or candidate["length"]
                    > current["length"]
                ):
                    records[
                        record_key
                    ] = candidate

        return records

    @staticmethod
    def _calculate_longest_streak(
        history: list[dict],
        condition,
    ) -> dict | None:
        best_length = 0
        best_start_index: int | None = None
        best_end_index: int | None = None

        current_length = 0
        current_start_index: int | None = None

        for (
            index,
            item,
        ) in enumerate(history):
            if condition(item):
                if current_length == 0:
                    current_start_index = index

                current_length += 1

                if current_length > best_length:
                    best_length = (
                        current_length
                    )

                    best_start_index = (
                        current_start_index
                    )

                    best_end_index = index

            else:
                current_length = 0
                current_start_index = None

        if (
            best_length <= 0
            or best_start_index is None
            or best_end_index is None
        ):
            return None

        start = history[
            best_start_index
        ]

        end = history[
            best_end_index
        ]

        return {
            "length": best_length,
            "start_match_id": (
                start["match_id"]
            ),
            "end_match_id": (
                end["match_id"]
            ),
            "start_matchday": (
                start["matchday"]
            ),
            "end_matchday": (
                end["matchday"]
            ),
            "start_date": (
                start["match_date"]
            ),
            "end_date": (
                end["match_date"]
            ),
        }

    @staticmethod
    def _get_biggest_home_win(
        matches: list[dict],
    ) -> dict | None:
        candidates = [
            match
            for match in matches
            if (
                match["home_goals"]
                > match["away_goals"]
            )
        ]

        if not candidates:
            return None

        match = max(
            candidates,
            key=lambda item: (
                item["home_goals"]
                - item["away_goals"],
                item["home_goals"],
            ),
        )

        return RecordsService._match_record(
            match
        )

    @staticmethod
    def _get_biggest_away_win(
        matches: list[dict],
    ) -> dict | None:
        candidates = [
            match
            for match in matches
            if (
                match["away_goals"]
                > match["home_goals"]
            )
        ]

        if not candidates:
            return None

        match = max(
            candidates,
            key=lambda item: (
                item["away_goals"]
                - item["home_goals"],
                item["away_goals"],
            ),
        )

        return RecordsService._match_record(
            match
        )

    @staticmethod
    def _get_biggest_win(
        matches: list[dict],
    ) -> dict | None:
        candidates = [
            match
            for match in matches
            if (
                match["home_goals"]
                != match["away_goals"]
            )
        ]

        if not candidates:
            return None

        match = max(
            candidates,
            key=lambda item: (
                abs(
                    item["home_goals"]
                    - item["away_goals"]
                ),
                max(
                    item["home_goals"],
                    item["away_goals"],
                ),
            ),
        )

        return RecordsService._match_record(
            match
        )

    @staticmethod
    def _get_highest_scoring_match(
        matches: list[dict],
    ) -> dict | None:
        if not matches:
            return None

        match = max(
            matches,
            key=lambda item: (
                item["home_goals"]
                + item["away_goals"],
                abs(
                    item["home_goals"]
                    - item["away_goals"]
                ),
            ),
        )

        result = (
            RecordsService._match_record(
                match
            )
        )

        result["total_goals"] = (
            match["home_goals"]
            + match["away_goals"]
        )

        return result

    @staticmethod
    def _get_most_home_goals_match(
        matches: list[dict],
    ) -> dict | None:
        if not matches:
            return None

        match = max(
            matches,
            key=lambda item: (
                item["home_goals"],
                item["home_goals"]
                + item["away_goals"],
            ),
        )

        return RecordsService._match_record(
            match
        )

    @staticmethod
    def _get_most_away_goals_match(
        matches: list[dict],
    ) -> dict | None:
        if not matches:
            return None

        match = max(
            matches,
            key=lambda item: (
                item["away_goals"],
                item["home_goals"]
                + item["away_goals"],
            ),
        )

        return RecordsService._match_record(
            match
        )

    @staticmethod
    def _get_highest_scoring_draw(
        matches: list[dict],
    ) -> dict | None:
        candidates = [
            match
            for match in matches
            if (
                match["home_goals"]
                == match["away_goals"]
            )
        ]

        if not candidates:
            return None

        match = max(
            candidates,
            key=lambda item: (
                item["home_goals"]
                + item["away_goals"],
                item["home_goals"],
            ),
        )

        result = (
            RecordsService._match_record(
                match
            )
        )

        result["total_goals"] = (
            match["home_goals"]
            + match["away_goals"]
        )

        return result

    @staticmethod
    def _get_team_record(
        statistics: list[dict],
        key: str,
        highest: bool,
    ) -> dict | None:
        played_statistics = [
            row
            for row in statistics
            if row["played"] > 0
        ]

        if not played_statistics:
            return None

        selector = (
            max
            if highest
            else min
        )

        row = selector(
            played_statistics,
            key=lambda item: int(
                item[key]
            ),
        )

        return {
            "team_id": row[
                "team_id"
            ],
            "team_name": row[
                "team_name"
            ],
            "played": row[
                "played"
            ],
            "value": int(
                row[key]
            ),
        }

    @staticmethod
    def _match_record(
        match: dict,
    ) -> dict:
        return {
            "match_id": match[
                "match_id"
            ],
            "matchday": match[
                "matchday"
            ],
            "match_date": match[
                "match_date"
            ],
            "home_team_id": match[
                "home_team_id"
            ],
            "home_team_name": match[
                "home_team_name"
            ],
            "away_team_id": match[
                "away_team_id"
            ],
            "away_team_name": match[
                "away_team_name"
            ],
            "home_goals": match[
                "home_goals"
            ],
            "away_goals": match[
                "away_goals"
            ],
            "goal_difference": abs(
                match["home_goals"]
                - match["away_goals"]
            ),
        }