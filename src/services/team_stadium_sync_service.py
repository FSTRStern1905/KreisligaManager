import sqlite3


class TeamStadiumSyncService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def sync_all(
        self,
    ) -> dict:
        competition_rows = self.cursor.execute(
            """
            SELECT DISTINCT competition_id
            FROM matches
            WHERE
                competition_id IS NOT NULL
                AND stadium_id IS NOT NULL
            ORDER BY competition_id;
            """
        ).fetchall()

        competitions = 0
        assignments = 0

        for row in competition_rows:
            result = self.sync_competition(
                int(row[0])
            )
            competitions += 1
            assignments += result["assignments"]

        return {
            "competitions": competitions,
            "assignments": assignments,
        }

    def sync_competition(
        self,
        competition_id: int,
    ) -> dict:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        usage_rows = self.cursor.execute(
            """
            SELECT
                home_team_id,
                stadium_id,
                COUNT(*) AS home_matches
            FROM matches
            WHERE
                competition_id = ?
                AND stadium_id IS NOT NULL
            GROUP BY
                home_team_id,
                stadium_id
            ORDER BY
                home_team_id,
                home_matches DESC,
                stadium_id;
            """,
            (competition_id,),
        ).fetchall()

        usage_by_team: dict[
            int,
            list[tuple[int, int]],
        ] = {}

        for row in usage_rows:
            team_id = int(row[0])
            stadium_id = int(row[1])
            home_matches = int(row[2])

            usage_by_team.setdefault(
                team_id,
                [],
            ).append(
                (
                    stadium_id,
                    home_matches,
                )
            )

        self.cursor.execute(
            """
            DELETE FROM team_stadiums
            WHERE competition_id = ?;
            """,
            (competition_id,),
        )

        assignments = 0
        teams = 0

        for team_id, usages in usage_by_team.items():
            if not usages:
                continue

            teams += 1

            max_home_matches = max(
                home_matches
                for _, home_matches in usages
            )

            for stadium_id, home_matches in usages:
                role = (
                    "main"
                    if home_matches == max_home_matches
                    else "alternate"
                )

                self.cursor.execute(
                    """
                    INSERT INTO team_stadiums (
                        team_id,
                        stadium_id,
                        competition_id,
                        role,
                        home_matches
                    )
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        team_id,
                        stadium_id,
                        competition_id,
                        role,
                        home_matches,
                    ),
                )

                assignments += 1

        self.connection.commit()

        return {
            "competition_id": competition_id,
            "teams": teams,
            "assignments": assignments,
        }
