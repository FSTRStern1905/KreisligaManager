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
            key=lambda item: item[1].team_player_factor,
            reverse=True,
        )

        print("=" * 125)
        print("TEAM PLAYER STRENGTH – PLAUSIBILITY TEST")
        print("=" * 125)
        print(f"Wettbewerb-ID:       {COMPETITION_ID}")
        print(f"Cutoff-Spieltag:     {CUTOFF_MATCHDAY}")
        print(f"Erlaubte Historie:   Spieltage < {CUTOFF_MATCHDAY}")
        print(f"Kernkadergröße:      {CORE_SIZE}")
        print(f"Teams gefunden:      {len(results)}")
        print()

        print(
            f"{'#':>2} "
            f"{'Team':<30} "
            f"{'Spieler':>7} "
            f"{'Kern':>5} "
            f"{'Min':>6} "
            f"{'Kern-Min':>8} "
            f"{'Kern-%':>7} "
            f"{'Weighted':>9} "
            f"{'Top5':>7} "
            f"{'Stabil':>7} "
            f"{'Factor':>7}"
        )
        print("-" * 125)

        for index, (team_name, strength) in enumerate(
            results,
            start=1,
        ):
            print(
                f"{index:>2} "
                f"{team_name[:30]:<30} "
                f"{strength.historical_players:>7} "
                f"{strength.core_players:>5} "
                f"{strength.total_minutes:>6} "
                f"{strength.core_minutes:>8} "
                f"{strength.core_minutes_share * 100:>6.1f}% "
                f"{strength.weighted_player_strength:>9.3f} "
                f"{strength.top_player_strength:>7.3f} "
                f"{strength.squad_stability:>7.3f} "
                f"{strength.team_player_factor:>7.3f}"
            )

        if results:
            factors = [
                strength.team_player_factor
                for _, strength in results
            ]
            weighted = [
                strength.weighted_player_strength
                for _, strength in results
            ]
            stability = [
                strength.squad_stability
                for _, strength in results
            ]

            print()
            print("=" * 125)
            print("RANGES")
            print("=" * 125)
            print(
                f"Team Player Factor: "
                f"{min(factors):.3f} – {max(factors):.3f}"
            )
            print(
                f"Weighted Strength:  "
                f"{min(weighted):.3f} – {max(weighted):.3f}"
            )
            print(
                f"Squad Stability:    "
                f"{min(stability):.3f} – {max(stability):.3f}"
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
