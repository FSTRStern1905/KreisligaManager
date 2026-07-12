import random
import sqlite3
from datetime import date, timedelta


class DemoMatchSimulator:
    def __init__(
        self,
        connection: sqlite3.Connection,
        seed: int = 2028,
    ):
        self.connection = connection
        self.cursor = connection.cursor()
        self.random = random.Random(seed)

    def simulate_competition(
        self,
        competition_id: int,
    ) -> dict:
        matches = self._load_matches(competition_id)

        if not matches:
            raise ValueError(
                "Für den Wettbewerb wurden keine Spiele gefunden."
            )

        stadium_ids = self._load_stadium_ids()
        referee_ids = self._load_referee_ids()

        if not stadium_ids:
            raise ValueError("Es sind keine Stadien vorhanden.")

        if not referee_ids:
            raise ValueError("Es sind keine Schiedsrichter vorhanden.")

        first_matchday = date(2026, 8, 9)

        for match in matches:
            match_id = match[0]
            matchday = match[1]

            match_date = first_matchday + timedelta(
                days=(matchday - 1) * 7
            )

            kickoff_time = self.random.choice(
                [
                    "13:00",
                    "14:30",
                    "15:00",
                    "16:00",
                    "17:30",
                ]
            )

            home_goals = self._generate_goals(
                home_advantage=True
            )
            away_goals = self._generate_goals(
                home_advantage=False
            )

            stadium_id = self.random.choice(stadium_ids)
            referee_id = self.random.choice(referee_ids)
            attendance = self.random.randint(45, 650)

            self.cursor.execute(
                """
                UPDATE matches
                SET
                    match_date = ?,
                    kickoff_time = ?,
                    stadium_id = ?,
                    referee_id = ?,
                    attendance = ?,
                    home_goals = ?,
                    away_goals = ?,
                    status = 'finished'
                WHERE match_id = ?
                """,
                (
                    match_date.isoformat(),
                    kickoff_time,
                    stadium_id,
                    referee_id,
                    attendance,
                    home_goals,
                    away_goals,
                    match_id,
                ),
            )

        self.connection.commit()

        return {
            "match_count": len(matches),
            "finished_count": len(matches),
        }

    def _load_matches(
        self,
        competition_id: int,
    ) -> list[tuple]:
        self.cursor.execute(
            """
            SELECT
                match_id,
                matchday
            FROM matches
            WHERE competition_id = ?
            ORDER BY
                matchday,
                match_id
            """,
            (competition_id,),
        )

        return self.cursor.fetchall()

    def _load_stadium_ids(self) -> list[int]:
        self.cursor.execute(
            """
            SELECT stadium_id
            FROM stadiums
            ORDER BY stadium_id
            """
        )

        return [
            row[0]
            for row in self.cursor.fetchall()
        ]

    def _load_referee_ids(self) -> list[int]:
        self.cursor.execute(
            """
            SELECT referee_id
            FROM referees
            ORDER BY referee_id
            """
        )

        return [
            row[0]
            for row in self.cursor.fetchall()
        ]

    def _generate_goals(
        self,
        home_advantage: bool,
    ) -> int:
        values = [
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            2,
            2,
            2,
            3,
            3,
            4,
            5,
        ]

        goals = self.random.choice(values)

        if (
            home_advantage
            and self.random.random() < 0.22
        ):
            goals += 1

        return min(goals, 8)