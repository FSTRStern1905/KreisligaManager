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
TOP_N = 20


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

        rows = _get_players_with_history(
            connection=connection,
            competition_id=COMPETITION_ID,
            cutoff_matchday=CUTOFF_MATCHDAY,
        )

        strengths = []

        for row in rows:
            strength = service.get_player_strength(
                int(row["player_id"])
            )
            strengths.append(
                (
                    strength,
                    _player_name(row),
                    str(row["team_name"]),
                    str(row["position"] or ""),
                )
            )

        strengths.sort(
            key=lambda item: (
                item[0].overall_factor,
                item[0].minutes_played,
            ),
            reverse=True,
        )

        print("=" * 140)
        print("PLAYER STRENGTH PLAUSIBILITY TEST")
        print("=" * 140)
        print(f"Wettbewerb-ID:      {COMPETITION_ID}")
        print(f"Cutoff-Spieltag:    {CUTOFF_MATCHDAY}")
        print(
            f"Erlaubte Historie:  Spieltage < "
            f"{CUTOFF_MATCHDAY}"
        )
        print(f"Spieler gefunden:   {len(strengths)}")
        print()

        print(
            f"{'Spieler':<28} "
            f"{'Team':<26} "
            f"{'Pos':<8} "
            f"{'Sp':>3} "
            f"{'St':>3} "
            f"{'Min':>5} "
            f"{'T':>3} "
            f"{'A':>3} "
            f"{'T/90':>6} "
            f"{'A/90':>6} "
            f"{'Avail':>7} "
            f"{'Attack':>7} "
            f"{'Exp':>7} "
            f"{'Overall':>7}"
        )
        print("-" * 140)

        for strength, name, team, position in strengths[:TOP_N]:
            print(
                f"{name[:28]:<28} "
                f"{team[:26]:<26} "
                f"{position[:8]:<8} "
                f"{strength.matches_played:>3} "
                f"{strength.starts:>3} "
                f"{strength.minutes_played:>5} "
                f"{strength.goals:>3} "
                f"{strength.assists:>3} "
                f"{strength.goals_per_90:>6.2f} "
                f"{strength.assists_per_90:>6.2f} "
                f"{strength.availability_factor:>7.3f} "
                f"{strength.attacking_factor:>7.3f} "
                f"{strength.experience_factor:>7.3f} "
                f"{strength.overall_factor:>7.3f}"
            )

        print()
        print("=" * 140)
        print("RANGES")
        print("=" * 140)

        if strengths:
            overall = [
                item[0].overall_factor
                for item in strengths
            ]
            attack = [
                item[0].attacking_factor
                for item in strengths
            ]
            availability = [
                item[0].availability_factor
                for item in strengths
            ]

            print(
                f"Overall:      "
                f"{min(overall):.3f} – "
                f"{max(overall):.3f}"
            )
            print(
                f"Attack:       "
                f"{min(attack):.3f} – "
                f"{max(attack):.3f}"
            )
            print(
                f"Availability: "
                f"{min(availability):.3f} – "
                f"{max(availability):.3f}"
            )

    finally:
        connection.close()


def _get_players_with_history(
    connection: sqlite3.Connection,
    competition_id: int,
    cutoff_matchday: int,
):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT DISTINCT
            players.player_id,
            players.first_name,
            players.last_name,
            players.position,
            teams.name AS team_name
        FROM player_match_stats
        INNER JOIN players
            ON players.player_id = player_match_stats.player_id
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
        ORDER BY
            teams.name,
            players.last_name,
            players.first_name;
        """,
        (
            competition_id,
            cutoff_matchday,
        ),
    )
    return cursor.fetchall()


def _player_name(row) -> str:
    first_name = str(row["first_name"] or "").strip()
    last_name = str(row["last_name"] or "").strip()

    return " ".join(
        part
        for part in (first_name, last_name)
        if part
    )


if __name__ == "__main__":
    main()
