from __future__ import annotations

import sqlite3


class PlayerStatisticsService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_player_statistics(
        self,
        competition_id: int,
        player_id: int,
    ) -> dict | None:
        self._validate_id(
            competition_id,
            "Wettbewerb",
        )
        self._validate_id(
            player_id,
            "Spieler",
        )

        query = self._build_statistics_query(
            include_team_filter=False,
        )

        query += '''
            AND players.player_id = ?

            GROUP BY
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.team_id,
                teams.name,
                teams.short_name

            ORDER BY
                COUNT(
                    player_match_stats.player_match_stat_id
                ) DESC,
                teams.team_id

            LIMIT 1;
        '''

        self.cursor.execute(
            query,
            (
                competition_id,
                player_id,
            ),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return self._row_to_statistics(
            row
        )

    def get_competition_statistics(
        self,
        competition_id: int,
        team_id: int | None = None,
        minimum_minutes: int = 0,
        limit: int | None = None,
    ) -> list[dict]:
        self._validate_id(
            competition_id,
            "Wettbewerb",
        )

        if team_id is not None:
            self._validate_id(
                team_id,
                "Mannschaft",
            )

        if minimum_minutes < 0:
            raise ValueError(
                "Die Mindestspielzeit darf nicht "
                "negativ sein."
            )

        if limit is not None and limit <= 0:
            raise ValueError(
                "Das Limit muss größer als 0 sein."
            )

        query = self._build_statistics_query(
            include_team_filter=(
                team_id is not None
            ),
        )

        parameters: list[int] = [
            competition_id
        ]

        if team_id is not None:
            parameters.append(
                team_id
            )

        query += '''
            GROUP BY
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,
                teams.team_id,
                teams.name,
                teams.short_name

            HAVING
                SUM(
                    player_match_stats.minutes_played
                ) >= ?

            ORDER BY
                goals DESC,
                assists DESC,
                minutes_played DESC,
                appearances DESC,
                players.last_name COLLATE NOCASE,
                players.first_name COLLATE NOCASE
        '''

        parameters.append(
            minimum_minutes
        )

        if limit is not None:
            query += '''
                LIMIT ?
            '''
            parameters.append(
                limit
            )

        self.cursor.execute(
            query,
            tuple(parameters),
        )

        return [
            self._row_to_statistics(row)
            for row in self.cursor.fetchall()
        ]

    def get_top_scorers(
        self,
        competition_id: int,
        limit: int = 10,
    ) -> list[dict]:
        return self.get_competition_statistics(
            competition_id=competition_id,
            limit=limit,
        )

    def get_team_statistics(
        self,
        competition_id: int,
        team_id: int,
    ) -> list[dict]:
        return self.get_competition_statistics(
            competition_id=competition_id,
            team_id=team_id,
        )

    def get_player_match_history(
        self,
        competition_id: int,
        player_id: int,
    ) -> list[dict]:
        self._validate_id(
            competition_id,
            "Wettbewerb",
        )
        self._validate_id(
            player_id,
            "Spieler",
        )

        self.cursor.execute(
            '''
            SELECT
                matches.match_id,
                matches.matchday,
                matches.match_date,

                player_match_stats.team_id,
                teams.name,
                teams.short_name,

                player_match_stats.is_starting,
                player_match_stats.was_substituted_in,
                player_match_stats.was_substituted_out,
                player_match_stats.minute_in,
                player_match_stats.minute_out,
                player_match_stats.minutes_played,

                player_match_stats.goals,
                player_match_stats.own_goals,
                player_match_stats.assists,
                player_match_stats.yellow_cards,
                player_match_stats.yellow_red_cards,
                player_match_stats.red_cards,
                player_match_stats.clean_sheet,

                matches.home_team_id,
                home_teams.name,
                home_teams.short_name,

                matches.away_team_id,
                away_teams.name,
                away_teams.short_name,

                matches.home_goals,
                matches.away_goals

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            INNER JOIN teams
                ON teams.team_id =
                    player_match_stats.team_id

            INNER JOIN teams AS home_teams
                ON home_teams.team_id =
                    matches.home_team_id

            INNER JOIN teams AS away_teams
                ON away_teams.team_id =
                    matches.away_team_id

            WHERE
                matches.competition_id = ?
                AND player_match_stats.player_id = ?

            ORDER BY
                matches.matchday,
                matches.match_date,
                matches.match_id;
            ''',
            (
                competition_id,
                player_id,
            ),
        )

        return [
            self._row_to_match_history(row)
            for row in self.cursor.fetchall()
        ]

    @staticmethod
    def _build_statistics_query(
        include_team_filter: bool,
    ) -> str:
        query = '''
            SELECT
                players.player_id,
                players.first_name,
                players.last_name,
                players.position,

                teams.team_id,
                teams.name,
                teams.short_name,

                COUNT(
                    player_match_stats.player_match_stat_id
                ) AS squad_selections,

                SUM(
                    CASE
                        WHEN
                            player_match_stats.is_starting = 1
                            OR player_match_stats.was_substituted_in = 1
                            OR player_match_stats.minutes_played > 0
                        THEN 1
                        ELSE 0
                    END
                ) AS appearances,

                SUM(
                    player_match_stats.is_starting
                ) AS starts,

                SUM(
                    player_match_stats.was_substituted_in
                ) AS substituted_in,

                SUM(
                    player_match_stats.was_substituted_out
                ) AS substituted_out,

                SUM(
                    CASE
                        WHEN
                            player_match_stats.is_starting = 0
                            AND player_match_stats.was_substituted_in = 0
                            AND player_match_stats.minutes_played = 0
                        THEN 1
                        ELSE 0
                    END
                ) AS unused_bench,

                SUM(
                    player_match_stats.minutes_played
                ) AS minutes_played,

                SUM(
                    player_match_stats.goals
                ) AS goals,

                SUM(
                    player_match_stats.own_goals
                ) AS own_goals,

                SUM(
                    player_match_stats.assists
                ) AS assists,

                SUM(
                    player_match_stats.yellow_cards
                ) AS yellow_cards,

                SUM(
                    player_match_stats.yellow_red_cards
                ) AS yellow_red_cards,

                SUM(
                    player_match_stats.red_cards
                ) AS red_cards,

                SUM(
                    player_match_stats.clean_sheet
                ) AS clean_sheets

            FROM player_match_stats

            INNER JOIN matches
                ON matches.match_id =
                    player_match_stats.match_id

            INNER JOIN players
                ON players.player_id =
                    player_match_stats.player_id

            INNER JOIN teams
                ON teams.team_id =
                    player_match_stats.team_id

            WHERE
                matches.competition_id = ?
        '''

        if include_team_filter:
            query += '''
                AND teams.team_id = ?
            '''

        return query

    @staticmethod
    def _row_to_statistics(
        row: sqlite3.Row | tuple,
    ) -> dict:
        squad_selections = int(row[7] or 0)
        appearances = int(row[8] or 0)
        starts = int(row[9] or 0)
        substituted_in = int(row[10] or 0)
        substituted_out = int(row[11] or 0)
        unused_bench = int(row[12] or 0)
        minutes_played = int(row[13] or 0)
        goals = int(row[14] or 0)
        own_goals = int(row[15] or 0)
        assists = int(row[16] or 0)
        yellow_cards = int(row[17] or 0)
        yellow_red_cards = int(row[18] or 0)
        red_cards = int(row[19] or 0)
        clean_sheets = int(row[20] or 0)

        goals_per_90 = (
            round(
                goals * 90 / minutes_played,
                2,
            )
            if minutes_played > 0
            else 0.0
        )

        assists_per_90 = (
            round(
                assists * 90 / minutes_played,
                2,
            )
            if minutes_played > 0
            else 0.0
        )

        minutes_per_goal = (
            round(
                minutes_played / goals,
                1,
            )
            if goals > 0
            else None
        )

        average_minutes = (
            round(
                minutes_played / appearances,
                1,
            )
            if appearances > 0
            else 0.0
        )

        start_percentage = (
            round(
                starts * 100 / appearances,
                1,
            )
            if appearances > 0
            else 0.0
        )

        return {
            "player_id": int(row[0]),
            "player_name": (
                f"{row[1] or ''} "
                f"{row[2] or ''}"
            ).strip(),
            "first_name": row[1] or "",
            "last_name": row[2] or "",
            "position": row[3] or "-",

            "team_id": int(row[4]),
            "team_name": row[6] or row[5],

            "squad_selections": squad_selections,
            "appearances": appearances,
            "starts": starts,
            "substituted_in": substituted_in,
            "substituted_out": substituted_out,
            "unused_bench": unused_bench,

            "minutes_played": minutes_played,
            "average_minutes": average_minutes,

            "goals": goals,
            "own_goals": own_goals,
            "assists": assists,

            "yellow_cards": yellow_cards,
            "yellow_red_cards": yellow_red_cards,
            "red_cards": red_cards,
            "clean_sheets": clean_sheets,

            "goals_per_90": goals_per_90,
            "assists_per_90": assists_per_90,
            "minutes_per_goal": minutes_per_goal,
            "start_percentage": start_percentage,
        }

    @staticmethod
    def _row_to_match_history(
        row: sqlite3.Row | tuple,
    ) -> dict:
        return {
            "match_id": int(row[0]),
            "matchday": row[1],
            "match_date": row[2],

            "team_id": int(row[3]),
            "team_name": row[5] or row[4],

            "is_starting": bool(row[6]),
            "was_substituted_in": bool(row[7]),
            "was_substituted_out": bool(row[8]),
            "minute_in": row[9],
            "minute_out": row[10],
            "minutes_played": int(row[11] or 0),

            "goals": int(row[12] or 0),
            "own_goals": int(row[13] or 0),
            "assists": int(row[14] or 0),
            "yellow_cards": int(row[15] or 0),
            "yellow_red_cards": int(row[16] or 0),
            "red_cards": int(row[17] or 0),
            "clean_sheet": bool(row[18]),

            "home_team_id": int(row[19]),
            "home_team_name": row[21] or row[20],

            "away_team_id": int(row[22]),
            "away_team_name": row[24] or row[23],

            "home_goals": row[25],
            "away_goals": row[26],
        }

    @staticmethod
    def _validate_id(
        value: int,
        label: str,
    ) -> None:
        if value <= 0:
            raise ValueError(
                f"Ungültige {label}-ID."
            )