from __future__ import annotations

import sqlite3


class TeamPdfExportService:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    def get_competition_teams(
        self,
        competition_id: int,
    ) -> list[dict]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name,
                teams.short_name,
                teams.team_number
            FROM competition_teams
            INNER JOIN teams
                ON teams.team_id = competition_teams.team_id
            WHERE
                competition_teams.competition_id = ?
            ORDER BY
                teams.name COLLATE NOCASE ASC,
                teams.team_number ASC,
                teams.team_id ASC;
            """,
            (
                competition_id,
            ),
        )

        teams = []

        for row in self.cursor.fetchall():
            teams.append(
                {
                    "team_id": int(
                        row[0]
                    ),
                    "team_name": str(
                        row[1]
                    ),
                    "short_name": (
                        str(
                            row[2]
                        )
                        if row[2] is not None
                        else ""
                    ),
                    "team_number": (
                        int(
                            row[3]
                        )
                        if row[3] is not None
                        else None
                    ),
                }
            )

        return teams

    def get_team(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict | None:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerb-ID."
            )

        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschaft-ID."
            )

        self.cursor.execute(
            """
            SELECT
                teams.team_id,
                teams.name,
                teams.short_name,
                teams.team_number,
                teams.club_id
            FROM competition_teams
            INNER JOIN teams
                ON teams.team_id = competition_teams.team_id
            WHERE
                competition_teams.competition_id = ?
                AND competition_teams.team_id = ?
            LIMIT 1;
            """,
            (
                competition_id,
                team_id,
            ),
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return {
            "team_id": int(
                row[0]
            ),
            "team_name": str(
                row[1]
            ),
            "short_name": (
                str(
                    row[2]
                )
                if row[2] is not None
                else ""
            ),
            "team_number": (
                int(
                    row[3]
                )
                if row[3] is not None
                else None
            ),
            "club_id": int(
                row[4]
            ),
        }

    def validate_team_selection(
        self,
        competition_id: int,
        team_id: int,
    ) -> dict:
        team = self.get_team(
            competition_id=competition_id,
            team_id=team_id,
        )

        if team is None:
            raise ValueError(
                "Die ausgewählte Mannschaft gehört "
                "nicht zu diesem Wettbewerb."
            )

        return team
