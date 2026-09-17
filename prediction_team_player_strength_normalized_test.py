from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.player_strength_service import (
    PlayerStrengthService,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
CUTOFF_MATCHDAY = 10
CORE_SIZE = 14


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        context = HistoricalDataContext(
            connection=connection,
            competition_id=COMPETITION_ID,
            cutoff_matchday=CUTOFF_MATCHDAY,
        )
        service = PlayerStrengthService(context)

        teams = _get_teams(
            connection=connection,
            competition_id=COMPETITION_ID,
            cutoff_matchday=CUTOFF_MATCHDAY,
        )

        results = []

        for team in teams:
            strength = service.get_team_player_strength(
                team_id=int(team["team_id"]),
                core_size=CORE_SIZE,
            )
            results.append(
                (
                    str(team["team_name"]),
                    strength,
                )
            )

        results.sort(
            key=lambda item: (
                item[1].relative_team_player_factor
            ),
            reverse=True,
        )

        print("=" * 130)
        print("TEAM PLAYER STRENGTH – NORMALIZED TEST")
        print("=" * 130)
        print(f"Wettbewerb-ID:       {COMPETITION_ID}")
        print(f"Cutoff-Spieltag:     {CUTOFF_MATCHDAY}")
        print(f"Erlaubte Historie:   Spieltage < {CUTOFF_MATCHDAY}")
        print(f"Kernkadergröße:      {CORE_SIZE}")
        print(f"Teams gefunden:      {len(results)}")
        print()

        print(
            f"{'#':>2} "
            f"{'Team':<30} "
            f"{'Raw':>7} "
            f"{'Liga-Ø':>7} "
            f"{'Relativ':>8} "
            f"{'Abw.%':>7} "
            f"{'Weighted':>9} "
            f"{'Top5':>7} "
            f"{'Stabil':>7} "
            f"{'Kern-%':>7}"
        )
        print("-" * 130)

        for index, (team_name, strength) in enumerate(
            results,
            start=1,
        ):
            deviation = (
                strength.relative_team_player_factor - 1.0
            ) * 100.0

            print(
                f"{index:>2} "
                f"{team_name[:30]:<30} "
                f"{strength.team_player_factor:>7.3f} "
                f"{strength.league_average_player_factor:>7.3f} "
                f"{strength.relative_team_player_factor:>8.3f} "
                f"{deviation:>+6.2f}% "
                f"{strength.weighted_player_strength:>9.3f} "
                f"{strength.top_player_strength:>7.3f} "
                f"{strength.squad_stability:>7.3f} "
                f"{strength.core_minutes_share * 100:>6.1f}%"
            )

        if results:
            relative = [
                strength.relative_team_player_factor
                for _, strength in results
            ]
            raw = [
                strength.team_player_factor
                for _, strength in results
            ]
            league_average = results[
                0
            ][1].league_average_player_factor

            print()
            print("=" * 130)
            print("CHECK")
            print("=" * 130)
            print(
                f"Liga-Ø Raw Factor:       "
                f"{league_average:.6f}"
            )
            print(
                f"Ø relativer Faktor:      "
                f"{sum(relative) / len(relative):.6f}"
            )
            print(
                f"Relative Range:          "
                f"{min(relative):.3f} – "
                f"{max(relative):.3f}"
            )
            print(
                f"Raw Range:               "
                f"{min(raw):.3f} – "
                f"{max(raw):.3f}"
            )

            average_relative = (
                sum(relative) / len(relative)
            )

            if abs(average_relative - 1.0) < 0.000001:
                print(
                    "STATUS: OK – Liga-Normalisierung "
                    "liegt exakt bei 1.000."
                )
            else:
                print(
                    "STATUS: PRÜFEN – Liga-Ø weicht "
                    "von 1.000 ab."
                )

    finally:
        connection.close()


def _get_teams(
    connection: sqlite3.Connection,
    competition_id: int,
    cutoff_matchday: int,
):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT DISTINCT
            teams.team_id,
            teams.name AS team_name
        FROM player_match_stats
        INNER JOIN teams
            ON teams.team_id = player_match_stats.team_id
        INNER JOIN matches
            ON matches.match_id = player_match_stats.match_id
        WHERE
            matches.competition_id = ?
            AND matches.matchday IS NOT NULL
            AND matches.matchday < ?
            AND matches.home_goals IS NOT NULL
            AND matches.away_goals IS NOT NULL
        ORDER BY teams.name;
        """,
        (
            competition_id,
            cutoff_matchday,
        ),
    )
    return cursor.fetchall()


if __name__ == "__main__":
    main()
