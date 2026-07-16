import sqlite3

from src.services.statistics.table_service import TableService


class StatisticsService:
    FAIRPLAY_WEIGHTS = {
        "YELLOW_CARD": 1,
        "YELLOW_RED_CARD": 3,
        "RED_CARD": 5,
    }

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()
        self.table_service = TableService(connection)

    def get_competition_name(
        self,
        competition_id: int,
    ) -> str | None:
        self.cursor.execute(
            """
            SELECT name
            FROM competitions
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        result = self.cursor.fetchone()

        if result is None:
            return None

        return result[0]

    def get_table(
        self,
        competition_id: int,
        mode: str = "all",
    ) -> list[dict]:
        return self.table_service.get_table(
            competition_id=competition_id,
            mode=mode,
        )

    def get_top_scorers(
        self,
        competition_id: int,
        limit: int | None = None,
    ) -> list[dict]:
        query = """
            SELECT
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.team_id,
                teams.name,
                teams.short_name,
                COUNT(events.event_id) AS goal_count
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            INNER JOIN matches
                ON matches.match_id =
                   events.match_id
            INNER JOIN players
                ON players.player_id =
                   events.player_id
            INNER JOIN teams
                ON teams.team_id =
                   events.team_id
            WHERE
                matches.competition_id = ?
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL'
                )
            GROUP BY
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.team_id,
                teams.name,
                teams.short_name
            ORDER BY
                goal_count DESC,
                players.last_name ASC,
                players.first_name ASC
        """

        parameters: list = [competition_id]

        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)

        self.cursor.execute(
            query,
            parameters,
        )

        scorers = []

        for row in self.cursor.fetchall():
            first_name = row[1] or ""
            last_name = row[2] or ""

            scorers.append(
                {
                    "player_id": row[0],
                    "player_name": (
                        f"{first_name} {last_name}"
                    ).strip(),
                    "position": row[3] or "-",
                    "team_id": row[4],
                    "team_name": row[6] or row[5],
                    "goals": row[7],
                }
            )

        return scorers

    def get_fairplay_table(
        self,
        competition_id: int,
    ) -> list[dict]:
        teams = self._load_competition_teams(
            competition_id
        )

        fairplay = {}

        for team_id, team_name, short_name in teams:
            fairplay[team_id] = {
                "team_id": team_id,
                "team_name": short_name or team_name,
                "yellow_cards": 0,
                "yellow_red_cards": 0,
                "red_cards": 0,
                "fairplay_points": 0,
            }

        self.cursor.execute(
            """
            SELECT
                events.team_id,
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
                AND event_types.code IN (
                    'YELLOW_CARD',
                    'YELLOW_RED_CARD',
                    'RED_CARD'
                )
                AND events.team_id IS NOT NULL
            GROUP BY
                events.team_id,
                event_types.code
            """,
            (competition_id,),
        )

        for (
            team_id,
            event_code,
            card_count,
        ) in self.cursor.fetchall():
            if team_id not in fairplay:
                continue

            team = fairplay[team_id]

            if event_code == "YELLOW_CARD":
                team["yellow_cards"] = card_count

            elif event_code == "YELLOW_RED_CARD":
                team["yellow_red_cards"] = card_count

            elif event_code == "RED_CARD":
                team["red_cards"] = card_count

            team["fairplay_points"] += (
                card_count
                * self.FAIRPLAY_WEIGHTS[event_code]
            )

        result = list(fairplay.values())

        result.sort(
            key=lambda row: (
                row["fairplay_points"],
                row["red_cards"],
                row["yellow_red_cards"],
                row["yellow_cards"],
                row["team_name"].lower(),
            )
        )

        return result

    def get_finished_match_count(
        self,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE
                competition_id = ?
                AND status = 'finished'
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL
            """,
            (competition_id,),
        )

        return self.cursor.fetchone()[0]

    def get_goal_count(
        self,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(events.event_id)
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            INNER JOIN matches
                ON matches.match_id =
                   events.match_id
            WHERE
                matches.competition_id = ?
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL'
                )
            """,
            (competition_id,),
        )

        return self.cursor.fetchone()[0]

    def get_scorer_count(
        self,
        competition_id: int,
    ) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(DISTINCT events.player_id)
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            INNER JOIN matches
                ON matches.match_id =
                   events.match_id
            WHERE
                matches.competition_id = ?
                AND events.player_id IS NOT NULL
                AND event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL'
                )
            """,
            (competition_id,),
        )

        return self.cursor.fetchone()[0]

    def get_card_count(
        self,
        competition_id: int,
        event_code: str | None = None,
    ) -> int:
        query = """
            SELECT COUNT(events.event_id)
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            INNER JOIN matches
                ON matches.match_id =
                   events.match_id
            WHERE
                matches.competition_id = ?
                AND event_types.code IN (
                    'YELLOW_CARD',
                    'YELLOW_RED_CARD',
                    'RED_CARD'
                )
        """

        parameters: list = [competition_id]

        if event_code is not None:
            if event_code not in self.FAIRPLAY_WEIGHTS:
                raise ValueError(
                    f"Ungültiger Kartentyp: {event_code}"
                )

            query += """
                AND event_types.code = ?
            """

            parameters.append(event_code)

        self.cursor.execute(
            query,
            parameters,
        )

        return self.cursor.fetchone()[0]

    def _load_competition_teams(
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
                teams.name
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()