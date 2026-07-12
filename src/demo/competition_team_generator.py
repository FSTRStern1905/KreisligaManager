import sqlite3


class CompetitionTeamGenerator:
    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor

    def generate(
        self,
        competition_id: int,
        team_ids: list[int],
    ) -> int:
        if competition_id <= 0:
            raise ValueError("Ungültige Wettbewerb-ID.")

        if len(team_ids) < 2:
            raise ValueError(
                "Für einen Wettbewerb werden mindestens "
                "zwei Mannschaften benötigt."
            )

        self.cursor.execute(
            """
            DELETE FROM competition_teams
            WHERE competition_id = ?
            """,
            (competition_id,),
        )

        for team_id in team_ids:
            self.cursor.execute(
                """
                INSERT INTO competition_teams (
                    competition_id,
                    team_id
                )
                VALUES (?, ?)
                """,
                (
                    competition_id,
                    team_id,
                ),
            )

        return len(team_ids)