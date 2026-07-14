import sqlite3

from src.demo.stadiums import generate_demo_stadiums


class DemoStadiumGenerator:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def generate(self) -> int:
        stadiums = generate_demo_stadiums()

        for stadium in stadiums:
            self.cursor.execute(
                """
                DELETE FROM stadiums
                WHERE
                    name = ?
                    AND city = ?
                """,
                (
                    stadium.name,
                    stadium.city,
                ),
            )

            self.cursor.execute(
                """
                INSERT INTO stadiums (
                    name,
                    city,
                    capacity
                )
                VALUES (?, ?, ?)
                """,
                (
                    stadium.name,
                    stadium.city,
                    stadium.capacity,
                ),
            )

        return len(stadiums)