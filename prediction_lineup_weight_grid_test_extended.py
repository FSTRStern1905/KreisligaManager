from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService


DATABASE_PATH = Path("data/database/kreisligamanager.db")

COMPETITION_ID = 2
START_MATCHDAY = 5
END_MATCHDAY = 34

FORM_MATCHES = 6
FORM_WEIGHT = 0.20
OPPONENT_STRENGTH_WEIGHT = 1.25
PLAYER_STRENGTH_WEIGHT = 0.0

LINEUP_WEIGHTS = (
    0.00,
    0.50,
    1.00,
    1.50,
    2.00,
    2.50,
    3.00,
    4.00,
    5.00,
)


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 94)
        print("LINEUP WEIGHT GRID TEST – ERWEITERT – BUNDESLIGA 2025/26")
        print("=" * 94)
        print(f"Spieltage: {START_MATCHDAY}–{END_MATCHDAY}")
        print(
            f"Form: {FORM_MATCHES} Spiele / "
            f"Gewicht {FORM_WEIGHT:.2f}"
        )
        print(
            "Opponent Strength: "
            f"{OPPONENT_STRENGTH_WEIGHT:.2f}"
        )
        print(
            "PREMATCH Player Strength: "
            f"{PLAYER_STRENGTH_WEIGHT:.2f}"
        )
        print()

        results = []

        for lineup_weight in LINEUP_WEIGHTS:
            service = BacktestService(
                connection=connection,
                form_weight=FORM_WEIGHT,
                form_matches=FORM_MATCHES,
                opponent_strength_weight=OPPONENT_STRENGTH_WEIGHT,
                player_strength_weight=PLAYER_STRENGTH_WEIGHT,
                lineup_strength_weight=lineup_weight,
                minimum_lineup_players=11,
                minimum_known_lineup_players=8,
            )

            summary = service.run(
                competition_id=COMPETITION_ID,
                start_matchday=START_MATCHDAY,
                end_matchday=END_MATCHDAY,
            )

            result = (
                lineup_weight,
                summary.matches_tested,
                summary.correct_outcomes,
                summary.accuracy,
                summary.average_brier_score,
                summary.average_log_loss,
            )
            results.append(result)

            mode = "PREMATCH" if lineup_weight == 0.0 else "LINEUP"

            print(
                f"{mode:<8} "
                f"{lineup_weight:>4.2f} | "
                f"{summary.correct_outcomes:>3}/"
                f"{summary.matches_tested:<3} | "
                f"{summary.accuracy * 100:>6.2f}% | "
                f"Brier {summary.average_brier_score:.5f} | "
                f"LogLoss {summary.average_log_loss:.5f}"
            )

        baseline = results[0]

        print()
        print("=" * 94)
        print("DELTA GEGEN PREMATCH")
        print("=" * 94)

        for result in results[1:]:
            weight, matches, correct, accuracy, brier, log_loss = result

            print(
                f"Lineup {weight:>4.2f} | "
                f"Δ Treffer "
                f"{(accuracy - baseline[3]) * 100:+.2f} PP | "
                f"Δ Brier {brier - baseline[4]:+.6f} | "
                f"Δ LogLoss {log_loss - baseline[5]:+.6f} | "
                f"N={matches}"
            )

        best_brier = min(results, key=lambda row: row[4])
        best_log_loss = min(results, key=lambda row: row[5])
        best_accuracy = max(results, key=lambda row: row[3])

        print()
        print("=" * 94)
        print("BESTE WERTE IM GRID")
        print("=" * 94)
        print(
            f"Brier:       Gewicht {best_brier[0]:.2f} | "
            f"{best_brier[4]:.5f}"
        )
        print(
            f"LogLoss:     Gewicht {best_log_loss[0]:.2f} | "
            f"{best_log_loss[5]:.5f}"
        )
        print(
            f"Trefferquote: Gewicht {best_accuracy[0]:.2f} | "
            f"{best_accuracy[3] * 100:.2f}% "
            f"({best_accuracy[2]}/{best_accuracy[1]})"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
