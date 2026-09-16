from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
START_MATCHDAY = 5
END_MATCHDAY = 34

SMOOTHING_VALUES = (
    0.0,
    1.0,
    2.0,
    3.0,
    5.0,
    7.0,
    10.0,
    15.0,
)


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    original_smoothing = (
        TeamStrengthService.SMOOTHING_MATCHES
    )

    try:
        print("=" * 84)
        print("PREDICTION ENGINE – SMOOTHING PARAMETER TEST")
        print("=" * 84)
        print(f"Wettbewerb-ID:       {COMPETITION_ID}")
        print(
            f"Testzeitraum:         ST {START_MATCHDAY}–{END_MATCHDAY}"
        )
        print(
            f"Parameter:            {SMOOTHING_VALUES}"
        )
        print()

        results = []

        for smoothing in SMOOTHING_VALUES:
            TeamStrengthService.SMOOTHING_MATCHES = (
                smoothing
            )

            service = BacktestService(connection)

            summary = service.run(
                competition_id=COMPETITION_ID,
                start_matchday=START_MATCHDAY,
                end_matchday=END_MATCHDAY,
            )

            results.append(
                (
                    smoothing,
                    summary.matches_tested,
                    summary.correct_outcomes,
                    summary.accuracy,
                    summary.average_brier_score,
                )
            )

            print(
                f"Smoothing {smoothing:>4.1f}: "
                f"{summary.correct_outcomes:>3}/"
                f"{summary.matches_tested} | "
                f"{summary.accuracy * 100:>6.2f}% | "
                f"Brier {summary.average_brier_score:.4f}"
            )

        print()
        print("=" * 84)
        print("GESAMTVERGLEICH")
        print("=" * 84)
        print(
            f"{'Smooth':>7} | "
            f"{'Spiele':>6} | "
            f"{'Richtig':>7} | "
            f"{'Quote':>8} | "
            f"{'Brier':>7}"
        )
        print("-" * 84)

        for (
            smoothing,
            matches,
            correct,
            accuracy,
            brier,
        ) in results:
            print(
                f"{smoothing:>7.1f} | "
                f"{matches:>6} | "
                f"{correct:>7} | "
                f"{accuracy * 100:>7.2f}% | "
                f"{brier:>7.4f}"
            )

        best_brier = min(
            results,
            key=lambda item: item[4],
        )
        best_accuracy = max(
            results,
            key=lambda item: item[3],
        )

        print()
        print("=" * 84)
        print("BESTE PARAMETER")
        print("=" * 84)
        print(
            "Niedrigster Brier:   "
            f"Smoothing {best_brier[0]:.1f} | "
            f"{best_brier[4]:.4f} | "
            f"{best_brier[3] * 100:.2f}% 1X2"
        )
        print(
            "Höchste 1X2-Quote:   "
            f"Smoothing {best_accuracy[0]:.1f} | "
            f"{best_accuracy[3] * 100:.2f}% | "
            f"Brier {best_accuracy[4]:.4f}"
        )

        print()
        print(
            "Hinweis: Der Parameter wird durch diesen Test "
            "nicht dauerhaft verändert."
        )

    finally:
        TeamStrengthService.SMOOTHING_MATCHES = (
            original_smoothing
        )
        connection.close()


if __name__ == "__main__":
    main()
