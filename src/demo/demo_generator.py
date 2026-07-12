import random
import sqlite3
from pathlib import Path

from src.database.schema import DatabaseSchema
from src.demo.clubs import DEMO_CLUBS
from src.demo.competition_generator import CompetitionGenerator
from src.demo.competition_team_generator import (
    CompetitionTeamGenerator,
)
from src.demo.match_simulator import DemoMatchSimulator
from src.demo.players import generate_players_for_club
from src.demo.referees import generate_demo_referees
from src.demo.schedule_generator import DemoScheduleGenerator
from src.demo.stadiums import generate_demo_stadiums


DATABASE_PATH = Path("data/database/kreisligamanager.db")


class DemoGenerator:
    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = database_path

    def run(self):
        print("Demo-Daten werden erstellt...")

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()

        try:
            schema = DatabaseSchema(connection)
            schema.create_all_tables()

            team_ids = self._insert_clubs_and_teams(cursor)

            player_count = self._insert_players(
                cursor,
                team_ids,
            )

            stadium_count = self._insert_stadiums(cursor)
            referee_count = self._insert_referees(cursor)

            competition_generator = CompetitionGenerator(cursor)
            competition_id = competition_generator.generate()

            competition_team_generator = (
                CompetitionTeamGenerator(cursor)
            )

            competition_team_count = (
                competition_team_generator.generate(
                    competition_id=competition_id,
                    team_ids=list(team_ids.values()),
                )
            )

            connection.commit()

            schedule_generator = DemoScheduleGenerator(connection)

            schedule_result = schedule_generator.generate(
                competition_id
            )

            match_simulator = DemoMatchSimulator(connection)

            simulation_result = (
                match_simulator.simulate_competition(
                    competition_id
                )
            )

            connection.commit()

            print("Demo-Daten erfolgreich erstellt.")
            print(f"Vereine: {len(DEMO_CLUBS)}")
            print(f"Mannschaften: {len(team_ids)}")
            print(f"Spieler: {player_count}")
            print(f"Stadien: {stadium_count}")
            print(f"Schiedsrichter: {referee_count}")
            print(f"Wettbewerb-ID: {competition_id}")
            print(
                "Wettbewerbsteilnehmer: "
                f"{competition_team_count}"
            )
            print(
                "Spieltage: "
                f"{schedule_result['matchday_count']}"
            )
            print(
                "Spiele: "
                f"{schedule_result['match_count']}"
            )
            print(
                "Simulierte Spiele: "
                f"{simulation_result['finished_count']}"
            )

        except Exception:
            connection.rollback()
            print("Fehler beim Erstellen der Demo-Daten.")
            raise

        finally:
            connection.close()

    def _insert_clubs_and_teams(
        self,
        cursor: sqlite3.Cursor,
    ) -> dict[str, int]:
        team_ids = {}

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

            club_result = cursor.fetchone()

            if club_result is None:
                raise ValueError(
                    "Verein konnte nicht gefunden werden: "
                    f"{club.name}"
                )

            club_id = club_result[0]

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

            cursor.execute(
                """
                SELECT team_id
                FROM teams
                WHERE
                    club_id = ?
                    AND team_number = ?
                """,
                (
                    club_id,
                    1,
                ),
            )

            team_result = cursor.fetchone()

            if team_result is None:
                raise ValueError(
                    "Mannschaft konnte nicht gefunden werden: "
                    f"{club.name}"
                )

            team_ids[club.name] = team_result[0]

        return team_ids

    def _insert_players(
        self,
        cursor: sqlite3.Cursor,
        team_ids: dict[str, int],
    ) -> int:
        cursor.execute(
            """
            DELETE FROM players
            WHERE team_id IS NULL
            """
        )

        player_count = 0

        for club_index, club in enumerate(
            DEMO_CLUBS,
            start=1,
        ):
            team_id = team_ids[club.name]
            club_strength = 55 + club_index * 2

            players = generate_players_for_club(
                club_strength,
                club_index,
            )

            cursor.execute(
                """
                DELETE FROM players
                WHERE team_id = ?
                """,
                (team_id,),
            )

            for player in players:
                height_cm = self._generate_height(
                    player.position
                )

                weight_kg = self._generate_weight(
                    height_cm,
                    player.position,
                )

                cursor.execute(
                    """
                    INSERT INTO players (
                        team_id,
                        first_name,
                        last_name,
                        birthdate,
                        position,
                        shirt_number,
                        foot,
                        height_cm,
                        weight_kg,
                        nationality,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        team_id,
                        player.first_name,
                        player.last_name,
                        player.birthdate,
                        player.position,
                        player.number,
                        player.foot,
                        height_cm,
                        weight_kg,
                        "Deutschland",
                        1,
                    ),
                )

                player_count += 1

        return player_count

    def _insert_stadiums(
        self,
        cursor: sqlite3.Cursor,
    ) -> int:
        stadiums = generate_demo_stadiums()

        for stadium in stadiums:
            cursor.execute(
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

            cursor.execute(
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

    def _insert_referees(
        self,
        cursor: sqlite3.Cursor,
    ) -> int:
        referees = generate_demo_referees()

        cursor.execute(
            """
            DELETE FROM referees
            WHERE association = ?
            """,
            ("FVR",),
        )

        for referee in referees:
            cursor.execute(
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

    def _generate_height(
        self,
        position: str,
    ) -> int:
        if position == "Torwart":
            return random.randint(184, 198)

        if position in {
            "Innenverteidiger",
            "Stürmer",
        }:
            return random.randint(178, 194)

        return random.randint(168, 190)

    def _generate_weight(
        self,
        height_cm: int,
        position: str,
    ) -> int:
        base_weight = height_cm - 105

        if position in {
            "Torwart",
            "Innenverteidiger",
        }:
            base_weight += random.randint(4, 10)
        else:
            base_weight += random.randint(0, 7)

        return max(
            58,
            min(100, base_weight),
        )


if __name__ == "__main__":
    generator = DemoGenerator()
    generator.run()