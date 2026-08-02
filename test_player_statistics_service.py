import sqlite3

from src.services.statistics.player_statistics_service import (
    PlayerStatisticsService,
)


DATABASE_PATH = (
    "data/database/kreisligamanager.db"
)


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        service = PlayerStatisticsService(
            connection
        )

        competition_id = connection.execute(
            """
            SELECT competition_id
            FROM competitions
            ORDER BY competition_id
            LIMIT 1;
            """
        ).fetchone()[0]

        stats = service.get_competition_statistics(
            competition_id=competition_id,
            limit=20,
        )

        print("=" * 80)
        print("SPIELERSTATISTIKEN")
        print("=" * 80)

        for player in stats:
            print(
                player["player_name"],
                "|",
                player["team_name"],
                "| Einsätze:",
                player["appearances"],
                "| Startelf:",
                player["starts"],
                "| Minuten:",
                player["minutes_played"],
                "| Tore:",
                player["goals"],
                "| Tore/90:",
                player["goals_per_90"],
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()