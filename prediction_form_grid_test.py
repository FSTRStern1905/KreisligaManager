from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
START_MATCHDAY = 5
END_MATCHDAY = 34

STRENGTH_SMOOTHING = 5.0

FORM_MATCH_COUNTS = (
    3,
    4,
    5,
    6,
    8,
    10,
)

FORM_WEIGHTS = (
    0.00,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
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
        TeamStrengthService.SMOOTHING_MATCHES = (
            STRENGTH_SMOOTHING
        )

        print("=" * 100)
        print("PREDICTION ENGINE – FORM GRID TEST")
        print("=" * 100)
        print(f"Wettbewerb-ID:       {COMPETITION_ID}")
        print(
            f"Testzeitraum:         "
            f"ST {START_MATCHDAY}–{END_MATCHDAY}"
        )
        print(
            f"Strength-Smoothing:   "
            f"{STRENGTH_SMOOTHING}"
        )
        print(
            f"Form-Spiele:          "
            f"{FORM_MATCH_COUNTS}"
        )
        print(
            f"Form-Gewichte:        "
            f"{FORM_WEIGHTS}"
        )
        print()

        results: list[dict] = []

        total_tests = (
            len(FORM_MATCH_COUNTS)
            * len(FORM_WEIGHTS)
        )
        current_test = 0

        for form_matches in FORM_MATCH_COUNTS:
            for form_weight in FORM_WEIGHTS:
                current_test += 1

                service = BacktestService(
                    connection=connection,
                    form_weight=form_weight,
                    form_matches=form_matches,
                )

                summary = service.run(
                    competition_id=COMPETITION_ID,
                    start_matchday=START_MATCHDAY,
                    end_matchday=END_MATCHDAY,
                )

                result = {
                    "form_matches": form_matches,
                    "form_weight": form_weight,
                    "matches": summary.matches_tested,
                    "correct": summary.correct_outcomes,
                    "accuracy": summary.accuracy,
                    "brier": summary.average_brier_score,
                }
                results.append(result)

                print(
                    f"[{current_test:>2}/{total_tests}] "
                    f"Letzte {form_matches:>2} | "
                    f"Gewicht {form_weight:>4.2f} | "
                    f"{summary.correct_outcomes:>3}/"
                    f"{summary.matches_tested} | "
                    f"{summary.accuracy * 100:>6.2f}% | "
                    f"Brier "
                    f"{summary.average_brier_score:.4f}"
                )

        print()
        print("=" * 100)
        print("BRIER-MATRIX")
        print("=" * 100)

        header = "Spiele"
        for weight in FORM_WEIGHTS:
            header += f" | {weight:>6.2f}"
        print(header)
        print("-" * len(header))

        for form_matches in FORM_MATCH_COUNTS:
            row = f"{form_matches:>6}"

            for weight in FORM_WEIGHTS:
                result = _find_result(
                    results,
                    form_matches,
                    weight,
                )
                row += f" | {result['brier']:>6.4f}"

            print(row)

        print()
        print("=" * 100)
        print("1X2-MATRIX")
        print("=" * 100)

        header = "Spiele"
        for weight in FORM_WEIGHTS:
            header += f" | {weight:>6.2f}"
        print(header)
        print("-" * len(header))

        for form_matches in FORM_MATCH_COUNTS:
            row = f"{form_matches:>6}"

            for weight in FORM_WEIGHTS:
                result = _find_result(
                    results,
                    form_matches,
                    weight,
                )
                row += (
                    f" | "
                    f"{result['accuracy'] * 100:>5.2f}%"
                )

            print(row)

        baseline = _find_result(
            results,
            FORM_MATCH_COUNTS[0],
            0.0,
        )

        best_brier = min(
            results,
            key=lambda item: item["brier"],
        )

        best_accuracy = max(
            results,
            key=lambda item: (
                item["accuracy"],
                -item["brier"],
            ),
        )

        print()
        print("=" * 100)
        print("AUSWERTUNG")
        print("=" * 100)
        print(
            "Baseline ohne Form:"
        )
        print(
            f"  {baseline['correct']}/"
            f"{baseline['matches']} | "
            f"{baseline['accuracy'] * 100:.2f}% | "
            f"Brier {baseline['brier']:.4f}"
        )

        print()
        print(
            "Niedrigster Brier:"
        )
        print(
            f"  letzte "
            f"{best_brier['form_matches']} Spiele | "
            f"Gewicht "
            f"{best_brier['form_weight']:.2f} | "
            f"{best_brier['correct']}/"
            f"{best_brier['matches']} | "
            f"{best_brier['accuracy'] * 100:.2f}% | "
            f"Brier {best_brier['brier']:.4f}"
        )

        print()
        print(
            "Höchste 1X2-Quote:"
        )
        print(
            f"  letzte "
            f"{best_accuracy['form_matches']} Spiele | "
            f"Gewicht "
            f"{best_accuracy['form_weight']:.2f} | "
            f"{best_accuracy['correct']}/"
            f"{best_accuracy['matches']} | "
            f"{best_accuracy['accuracy'] * 100:.2f}% | "
            f"Brier {best_accuracy['brier']:.4f}"
        )

        print()
        print(
            "Bestes Brier-Modell vs. Baseline:"
        )
        print(
            f"  1X2:  "
            f"{(best_brier['accuracy'] - baseline['accuracy']) * 100:+.2f} "
            f"Prozentpunkte"
        )
        print(
            f"  Brier: "
            f"{best_brier['brier'] - baseline['brier']:+.4f}"
        )

        print()
        print(
            "Hinweis: Gewicht 0.00 ignoriert die Form. "
            "Die unterschiedlichen Fenster müssen dort "
            "identische Ergebnisse liefern."
        )

    finally:
        TeamStrengthService.SMOOTHING_MATCHES = (
            original_smoothing
        )
        connection.close()


def _find_result(
    results: list[dict],
    form_matches: int,
    form_weight: float,
) -> dict:
    for result in results:
        if (
            result["form_matches"] == form_matches
            and result["form_weight"] == form_weight
        ):
            return result

    raise RuntimeError(
        "Testergebnis nicht gefunden."
    )


if __name__ == "__main__":
    main()
