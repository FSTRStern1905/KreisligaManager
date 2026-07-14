import sqlite3
from pathlib import Path

from src.database.schema import DatabaseSchema
from src.demo.card_generator import DemoCardGenerator
from src.demo.club_generator import DemoClubGenerator
from src.demo.clubs import DEMO_CLUBS
from src.demo.competition_generator import CompetitionGenerator
from src.demo.competition_team_generator import (
    CompetitionTeamGenerator,
)
from src.demo.demo_cleanup import DemoCleanup
from src.demo.goal_generator import DemoGoalGenerator
from src.demo.match_simulator import DemoMatchSimulator
from src.demo.player_generator import DemoPlayerGenerator
from src.demo.referee_generator import DemoRefereeGenerator
from src.demo.schedule_generator import DemoScheduleGenerator
from src.demo.stadium_generator import DemoStadiumGenerator


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class DemoGenerator:
    def __init__(
        self,
        database_path: Path = DATABASE_PATH,
    ):
        self.database_path = database_path

    def run(self):
        print("Demo-Daten werden erstellt...")

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            self.database_path
        )

        try:
            schema = DatabaseSchema(connection)
            schema.create_all_tables()

            club_generator = DemoClubGenerator(
                connection
            )
            team_ids = club_generator.generate()

            competition_generator = CompetitionGenerator(
                connection.cursor()
            )
            competition_id = (
                competition_generator.generate()
            )

            cleanup = DemoCleanup(connection)
            cleanup.prepare_for_regeneration(
                competition_id=competition_id,
                team_ids=list(team_ids.values()),
            )

            player_generator = DemoPlayerGenerator(
                connection
            )
            player_count = player_generator.generate(
                team_ids
            )

            stadium_generator = DemoStadiumGenerator(
                connection
            )
            stadium_count = stadium_generator.generate()

            referee_generator = DemoRefereeGenerator(
                connection
            )
            referee_count = referee_generator.generate()

            competition_team_generator = (
                CompetitionTeamGenerator(
                    connection.cursor()
                )
            )

            competition_team_count = (
                competition_team_generator.generate(
                    competition_id=competition_id,
                    team_ids=list(team_ids.values()),
                )
            )

            connection.commit()

            schedule_generator = DemoScheduleGenerator(
                connection
            )
            schedule_result = schedule_generator.generate(
                competition_id
            )

            match_simulator = DemoMatchSimulator(
                connection
            )
            simulation_result = (
                match_simulator.simulate_competition(
                    competition_id
                )
            )

            goal_generator = DemoGoalGenerator(
                connection
            )
            goal_result = (
                goal_generator.generate_for_competition(
                    competition_id
                )
            )

            card_generator = DemoCardGenerator(
                connection
            )
            card_result = (
                card_generator.generate_for_competition(
                    competition_id
                )
            )

            connection.commit()

            self._print_summary(
                team_count=len(team_ids),
                player_count=player_count,
                stadium_count=stadium_count,
                referee_count=referee_count,
                competition_id=competition_id,
                competition_team_count=(
                    competition_team_count
                ),
                schedule_result=schedule_result,
                simulation_result=simulation_result,
                goal_result=goal_result,
                card_result=card_result,
            )

        except Exception:
            connection.rollback()

            print(
                "Fehler beim Erstellen der Demo-Daten."
            )

            raise

        finally:
            connection.close()

    def _print_summary(
        self,
        team_count: int,
        player_count: int,
        stadium_count: int,
        referee_count: int,
        competition_id: int,
        competition_team_count: int,
        schedule_result: dict,
        simulation_result: dict,
        goal_result: dict,
        card_result: dict,
    ):
        print("Demo-Daten erfolgreich erstellt.")
        print(f"Vereine: {len(DEMO_CLUBS)}")
        print(f"Mannschaften: {team_count}")
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

        print(
            "Tore: "
            f"{goal_result['goal_count']}"
        )

        print(
            "Gelbe Karten: "
            f"{card_result['yellow_cards']}"
        )

        print(
            "Gelb-Rote Karten: "
            f"{card_result['yellow_red_cards']}"
        )

        print(
            "Rote Karten: "
            f"{card_result['red_cards']}"
        )


if __name__ == "__main__":
    generator = DemoGenerator()
    generator.run()