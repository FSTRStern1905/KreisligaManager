import sqlite3
from pathlib import Path

from src.database.schema import DatabaseSchema
from src.demo.clubs import DEMO_CLUBS
from src.demo.players import generate_players_for_club


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class DemoGenerator:
    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = database_path

    def run(self):
        print("Demo-Daten werden erstellt...")

        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()

        try:
            schema = DatabaseSchema(connection)
            schema.create_all_tables()

            self._insert_clubs_and_teams(cursor)
            self._insert_players(cursor)

            connection.commit()

            print("Demo-Daten erfolgreich erstellt.")
            print(f"Vereine: {len(DEMO_CLUBS)}")
            print(f"Spieler: {len(DEMO_CLUBS) * 22}")

        except Exception as error:
            connection.rollback()
            print("Fehler beim Erstellen der Demo-Daten.")
            raise error

        finally:
            connection.close()

    def _insert_clubs_and_teams(self, cursor):
        for club in DEMO_CLUBS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO clubs (
                    name,
                    short_name,
                    city
                )
                VALUES (?, ?, ?)
                """,
                (
                    club.name,
                    club.short_name,
                    club.city,
                ),
            )

            cursor.execute(
                """
                SELECT club_id
                FROM clubs
                WHERE name = ?
                """,
                (club.name,),
            )

            result = cursor.fetchone()

            if result is None:
                raise ValueError(f"Verein konnte nicht gefunden werden: {club.name}")

            club_id = result[0]

            cursor.execute(
                """
                INSERT OR IGNORE INTO teams (
                    club_id,
                    name,
                    short_name,
                    team_number
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    club_id,
                    club.name,
                    club.short_name,
                    1,
                ),
            )

    def _insert_players(self, cursor):
        for club_index, club in enumerate(DEMO_CLUBS, start=1):
            club_strength = 55 + club_index * 2
            players = generate_players_for_club(club_strength, club_index)

            for player in players:
                cursor.execute(
                    """
                    INSERT INTO players (
                        first_name,
                        last_name,
                        birthdate,
                        position,
                        foot,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player.first_name,
                        player.last_name,
                        player.birthdate,
                        player.position,
                        player.foot,
                        1,
                    ),
                )


if __name__ == "__main__":
    generator = DemoGenerator()
    generator.run()