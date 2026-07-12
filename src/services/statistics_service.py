import sqlite3


class StatisticsService:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

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
    ) -> list[dict]:
        teams = self._load_competition_teams(
            competition_id
        )

        standings = {}

        for team_id, team_name, short_name in teams:
            standings[team_id] = {
                "team_id": team_id,
                "team_name": short_name or team_name,
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
            }

        matches = self._load_finished_matches(
            competition_id
        )

        for match in matches:
            home_team_id = match[0]
            away_team_id = match[1]
            home_goals = match[2]
            away_goals = match[3]

            if home_team_id not in standings:
                continue

            if away_team_id not in standings:
                continue

            home = standings[home_team_id]
            away = standings[away_team_id]

            home["played"] += 1
            away["played"] += 1

            home["goals_for"] += home_goals
            home["goals_against"] += away_goals

            away["goals_for"] += away_goals
            away["goals_against"] += home_goals

            if home_goals > away_goals:
                home["wins"] += 1
                home["points"] += 3
                away["losses"] += 1

            elif home_goals < away_goals:
                away["wins"] += 1
                away["points"] += 3
                home["losses"] += 1

            else:
                home["draws"] += 1
                away["draws"] += 1

                home["points"] += 1
                away["points"] += 1

        for row in standings.values():
            row["goal_difference"] = (
                row["goals_for"]
                - row["goals_against"]
            )

        result = list(standings.values())

        result.sort(
            key=lambda row: (
                -row["points"],
                -row["goal_difference"],
                -row["goals_for"],
                row["team_name"].lower(),
            )
        )

        return result

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
            WHERE competition_teams.competition_id = ?
            ORDER BY teams.name
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def _load_finished_matches(
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
                matchday,
                match_id
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()