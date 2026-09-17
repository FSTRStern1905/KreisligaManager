from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.lineup_strength_service import (
    LineupStrengthService,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
MATCHDAY = 10


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        context = HistoricalDataContext(
            connection=connection,
            competition_id=COMPETITION_ID,
            cutoff_matchday=MATCHDAY,
        )

        service = LineupStrengthService(context)

        fixtures = _get_fixtures(
            connection=connection,
            competition_id=COMPETITION_ID,
            matchday=MATCHDAY,
        )

        print("=" * 110)
        print("LINEUP STRENGTH PLAUSIBILITÄTSTEST")
        print("=" * 110)
        print(
            f"Wettbewerb-ID: {COMPETITION_ID} | "
            f"Ziel-Spieltag: {MATCHDAY}"
        )
        print(
            "Spielerstärken verwenden ausschließlich "
            f"Daten aus ST 1–{MATCHDAY - 1}."
        )
        print()

        if not fixtures:
            print("Keine Spiele gefunden.")
            return

        total_teams = 0
        complete_lineups = 0
        usable_lineups = 0

        for fixture in fixtures:
            print("-" * 110)
            print(
                f"{fixture['home_team_name']} - "
                f"{fixture['away_team_name']}"
            )
            print("-" * 110)

            for side, team_id, team_name in (
                (
                    "HEIM",
                    fixture["home_team_id"],
                    fixture["home_team_name"],
                ),
                (
                    "AUSW",
                    fixture["away_team_id"],
                    fixture["away_team_name"],
                ),
            ):
                result = service.get_lineup_strength(
                    match_id=fixture["match_id"],
                    team_id=team_id,
                )

                total_teams += 1

                if result.lineup_players >= 11:
                    complete_lineups += 1

                if result.known_players > 0:
                    usable_lineups += 1

                deviation = (
                    result.relative_lineup_factor - 1.0
                ) * 100.0

                print(
                    f"{side:<4} {team_name[:30]:<30} | "
                    f"XI {result.lineup_players:>2} | "
                    f"bekannt {result.known_players:>2} | "
                    f"Lineup {result.lineup_factor:.3f} | "
                    f"Erwartet {result.expected_lineup_factor:.3f} | "
                    f"Relativ {result.relative_lineup_factor:.3f} | "
                    f"{deviation:+6.2f}%"
                )

                if result.players:
                    top = sorted(
                        result.players,
                        key=lambda player: (
                            player.overall_factor,
                            player.minutes_played,
                        ),
                        reverse=True,
                    )[:3]

                    print(
                        "     Top: "
                        + " | ".join(
                            f"{player.player_name} "
                            f"{player.overall_factor:.3f}"
                            for player in top
                        )
                    )

            print()

        print("=" * 110)
        print("COVERAGE")
        print("=" * 110)
        print(f"Teams geprüft:          {total_teams}")
        print(
            f"Komplette Startelf:     "
            f"{complete_lineups}/{total_teams}"
        )
        print(
            f"Historisch auswertbar:  "
            f"{usable_lineups}/{total_teams}"
        )

    finally:
        connection.close()


def _get_fixtures(
    connection: sqlite3.Connection,
    competition_id: int,
    matchday: int,
) -> list[dict]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            matches.match_id,
            matches.home_team_id,
            matches.away_team_id,
            home_team.name AS home_team_name,
            away_team.name AS away_team_name
        FROM matches
        INNER JOIN teams AS home_team
            ON home_team.team_id = matches.home_team_id
        INNER JOIN teams AS away_team
            ON away_team.team_id = matches.away_team_id
        WHERE
            matches.competition_id = ?
            AND matches.matchday = ?
        ORDER BY matches.match_id;
        """,
        (
            competition_id,
            matchday,
        ),
    )

    return [
        dict(row)
        for row in cursor.fetchall()
    ]


if __name__ == "__main__":
    main()
