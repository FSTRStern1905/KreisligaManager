from __future__ import annotations

import sqlite3


class RecordsService:
    """
    Berechnet Wettbewerbsrekorde auf Basis abgeschlossener Spiele.

    Enthalten:
    - höchster Heimsieg
    - höchster Auswärtssieg
    - höchster Sieg insgesamt
    - torreichstes Spiel
    - beste Offensive
    - beste Defensive
    - schwächste Offensive
    - schwächste Defensive
    """

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
                matches.match_id ASC;
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

    def _build_team_statistics(
        self,
        competition_id: int,
        matches: list[dict],
    ) -> list[dict]:
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
                teams.name ASC;
            """,
            (competition_id,),
        )

        statistics: dict[int, dict] = {}

        for (
            team_id,
            team_name,
            short_name,
        ) in self.cursor.fetchall():
            statistics[int(team_id)] = {
                "team_id": int(
                    team_id
                ),
                "team_name": (
                    short_name
                    or team_name
                ),
                "played": 0,
                "goals_for": 0,
                "goals_against": 0,
            }

        for match in matches:
            home = statistics.get(
                match[
                    "home_team_id"
                ]
            )

            away = statistics.get(
                match[
                    "away_team_id"
                ]
            )

            if home is not None:
                home["played"] += 1
                home["goals_for"] += (
                    match[
                        "home_goals"
                    ]
                )
                home["goals_against"] += (
                    match[
                        "away_goals"
                    ]
                )

            if away is not None:
                away["played"] += 1
                away["goals_for"] += (
                    match[
                        "away_goals"
                    ]
                )
                away["goals_against"] += (
                    match[
                        "home_goals"
                    ]
                )

        return list(
            statistics.values()
        )

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
            RecordsService
            ._match_record(
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