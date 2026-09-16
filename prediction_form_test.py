from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
START_MATCHDAY = 5
END_MATCHDAY = 34

SMOOTHING_MATCHES = 5.0
FORM_MATCHES = 5

FORM_WEIGHTS = (
    0.0,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
    0.50,
)


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    original_smoothing = TeamStrengthService.SMOOTHING_MATCHES

    try:
        TeamStrengthService.SMOOTHING_MATCHES = SMOOTHING_MATCHES

        print("=" * 84)
        print("PREDICTION ENGINE – FORM PARAMETER TEST")
        print("=" * 84)
        print(f"Wettbewerb-ID:       {COMPETITION_ID}")
        print(f"Testzeitraum:         ST {START_MATCHDAY}–{END_MATCHDAY}")
        print(f"Strength-Smoothing:   {SMOOTHING_MATCHES}")
        print(f"Form-Spiele:          letzte {FORM_MATCHES}")
        print(f"Form-Gewichte:        {FORM_WEIGHTS}")
        print()

        results = []

        for form_weight in FORM_WEIGHTS:
            service = BacktestService(
                connection=connection,
                form_weight=form_weight,
                form_matches=FORM_MATCHES,
            )

            summary = service.run(
                competition_id=COMPETITION_ID,
                start_matchday=START_MATCHDAY,
                end_matchday=END_MATCHDAY,
            )

            results.append(
                (
                    form_weight,
                    summary.matches_tested,
                    summary.correct_outcomes,
                    summary.accuracy,
                    summary.average_brier_score,
                )
            )

            print(
                f"Form {form_weight:>4.2f}: "
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
            f"{'Form':>6} | "
            f"{'Spiele':>6} | "
            f"{'Richtig':>7} | "
            f"{'Quote':>8} | "
            f"{'Brier':>7}"
        )
        print("-" * 84)

        for (
            form_weight,
            matches,
            correct,
            accuracy,
            brier,
        ) in results:
            print(
                f"{form_weight:>6.2f} | "
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
            key=lambda item: (
                item[3],
                -item[4],
            ),
        )

        baseline = next(
            item
            for item in results
            if item[0] == 0.0
        )

        print()
        print("=" * 84)
        print("AUSWERTUNG")
        print("=" * 84)
        print(
            "Baseline ohne Form:  "
            f"{baseline[3] * 100:.2f}% | "
            f"Brier {baseline[4]:.4f}"
        )
        print(
            "Niedrigster Brier:   "
            f"Form {best_brier[0]:.2f} | "
            f"{best_brier[3] * 100:.2f}% | "
            f"Brier {best_brier[4]:.4f}"
        )
        print(
            "Höchste 1X2-Quote:   "
            f"Form {best_accuracy[0]:.2f} | "
            f"{best_accuracy[3] * 100:.2f}% | "
            f"Brier {best_accuracy[4]:.4f}"
        )

        brier_change = (
            best_brier[4] - baseline[4]
        )
        accuracy_change = (
            best_brier[3] - baseline[3]
        )

        print()
        print(
            "Bestes Brier-Modell vs. Baseline:"
        )
        print(
            f"  1X2:  {accuracy_change * 100:+.2f} Prozentpunkte"
        )
        print(
            f"  Brier: {brier_change:+.4f}"
        )

        print()
        print(
            "Der Test verändert die Modellparameter "
            "nicht dauerhaft."
        )

    finally:
        TeamStrengthService.SMOOTHING_MATCHES = original_smoothing
        connection.close()


if __name__ == "__main__":
    main()
