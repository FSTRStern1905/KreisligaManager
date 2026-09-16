from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
START_MATCHDAY = 5
END_MATCHDAY = 34


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        service = BacktestService(connection)

        print("=" * 84)
        print("PREDICTION ENGINE – BACKTEST v0.1")
        print("=" * 84)
        print(f"Wettbewerb-ID:       {COMPETITION_ID}")
        print(
            f"Testzeitraum:         ST {START_MATCHDAY}–{END_MATCHDAY}"
        )
        print(
            "Prinzip:              Jeder Spieltag kennt nur "
            "frühere Spieltage"
        )
        print()

        summary = service.run(
            competition_id=COMPETITION_ID,
            start_matchday=START_MATCHDAY,
            end_matchday=END_MATCHDAY,
        )

        print("=" * 84)
        print("ERGEBNIS PRO SPIELTAG")
        print("=" * 84)
        print(
            f"{'ST':>3} | {'Spiele':>6} | {'Richtig':>7} | "
            f"{'Quote':>7} | {'Brier':>7}"
        )
        print("-" * 84)

        for result in summary.matchdays:
            print(
                f"{result.matchday:>3} | "
                f"{result.matches_tested:>6} | "
                f"{result.correct_outcomes:>7} | "
                f"{result.accuracy * 100:>6.1f}% | "
                f"{result.average_brier_score:>7.4f}"
            )

        print()
        print("=" * 84)
        print("GESAMTERGEBNIS – BASELINE v0.1")
        print("=" * 84)
        print(
            f"Getestete Spiele:     {summary.matches_tested}"
        )
        print(
            f"1X2 richtig:          "
            f"{summary.correct_outcomes}/"
            f"{summary.matches_tested}"
        )
        print(
            f"Trefferquote:         "
            f"{summary.accuracy * 100:.2f}%"
        )
        print(
            f"Ø Brier Score:        "
            f"{summary.average_brier_score:.4f}"
        )

        print()
        print(
            "Je niedriger der Brier Score, desto besser "
            "sind die Wahrscheinlichkeiten kalibriert."
        )
        print(
            "Diese Werte sind unsere feste Baseline v0.1."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
