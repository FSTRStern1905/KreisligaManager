import sqlite3

from src.demo.referees import generate_demo_referees


class DemoRefereeGenerator:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def generate(self) -> int:
        referees = generate_demo_referees()

        self.cursor.execute(
            """
            DELETE FROM referees
            WHERE association = ?
            """,
            ("FVR",),
        )

        for referee in referees:
            self.cursor.execute(
                """
                INSERT INTO referees (
                    first_name,
                    last_name,
                    association
                )
                VALUES (?, ?, ?)
                """,
                (
                    referee.first_name,
                    referee.last_name,
                    referee.association,
                ),
            )

        return len(referees)