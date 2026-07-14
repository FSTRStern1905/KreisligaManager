import sqlite3


class DemoCleanup:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def prepare_for_regeneration(
        self,
        competition_id: int,
        team_ids: list[int],
    ):
        self.clear_competition_events(
            competition_id
        )

        self.clear_player_dependencies(
            team_ids
        )

        self.clear_competition_lineups(
            competition_id
        )

        self.clear_competition_weather(
            competition_id
        )

        self.clear_competition_formations(
            competition_id
        )

        self.clear_match_assignments(
            competition_id
        )

        self.connection.commit()

    def clear_player_dependencies(
        self,
        team_ids: list[int],
    ):
        if not team_ids:
            return

        placeholders = ",".join(
            "?"
            for _ in team_ids
        )

        self.cursor.execute(
            f"""
            DELETE FROM events
            WHERE
                player_id IN (
                    SELECT player_id
                    FROM players
                    WHERE team_id IN ({placeholders})
                )
                OR related_player_id IN (
                    SELECT player_id
                    FROM players
                    WHERE team_id IN ({placeholders})
                )
            """,
            (
                *team_ids,
                *team_ids,
            ),
        )

        self.cursor.execute(
            f"""
            DELETE FROM lineups
            WHERE player_id IN (
                SELECT player_id
                FROM players
                WHERE team_id IN ({placeholders})
            )
            """,
            team_ids,
        )

    def clear_competition_events(
        self,
        competition_id: int,
    ):
        self.cursor.execute(
            """
            DELETE FROM events
            WHERE match_id IN (
                SELECT match_id
                FROM matches
                WHERE competition_id = ?
            )
            """,
            (competition_id,),
        )

    def clear_competition_lineups(
        self,
        competition_id: int,
    ):
        self.cursor.execute(
            """
            DELETE FROM lineups
            WHERE match_id IN (
                SELECT match_id
                FROM matches
                WHERE competition_id = ?
            )
            """,
            (competition_id,),
        )

    def clear_competition_weather(
        self,
        competition_id: int,
    ):
        self.cursor.execute(
            """
            DELETE FROM weather
            WHERE match_id IN (
                SELECT match_id
                FROM matches
                WHERE competition_id = ?
            )
            """,
            (competition_id,),
        )

    def clear_competition_formations(
        self,
        competition_id: int,
    ):
        self.cursor.execute(
            """
            DELETE FROM match_formations
            WHERE match_id IN (
                SELECT match_id
                FROM matches
                WHERE competition_id = ?
            )
            """,
            (competition_id,),
        )

    def clear_match_assignments(
        self,
        competition_id: int,
    ):
        self.cursor.execute(
            """
            UPDATE matches
            SET
                stadium_id = NULL,
                referee_id = NULL
            WHERE competition_id = ?
            """,
            (competition_id,),
        )