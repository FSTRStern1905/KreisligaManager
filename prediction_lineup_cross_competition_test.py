from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService


DATABASE_PATH = Path("data/database/kreisligamanager.db")

COMPETITIONS = (
    (175, "Oberliga Rheinland-Pfalz/Saar", 5, 38),
    (2, "Bundesliga", 5, 34),
    (3, "Regionalliga Südwest", 5, 34),
    (1, "Kreisliga A7", 5, 26),
)

LINEUP_WEIGHTS = (
    0.00,
    1.00,
    1.50,
    2.00,
    3.00,
    4.00,
)

FORM_MATCHES = 6
FORM_WEIGHT = 0.20
OPPONENT_STRENGTH_WEIGHT = 1.25
PLAYER_STRENGTH_WEIGHT = 0.0

MINIMUM_LINEUP_PLAYERS = 11
MINIMUM_KNOWN_LINEUP_PLAYERS = 8


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 112)
        print("LINEUP CROSS-COMPETITION BACKTEST")
        print("=" * 112)
        print(
            f"Form: {FORM_MATCHES} / {FORM_WEIGHT:.2f} | "
            f"Opponent: {OPPONENT_STRENGTH_WEIGHT:.2f} | "
            f"PREMATCH Player: {PLAYER_STRENGTH_WEIGHT:.2f}"
        )
        print(
            f"LINEUP Mindestabdeckung: "
            f"{MINIMUM_LINEUP_PLAYERS}/11 Starter | "
            f"{MINIMUM_KNOWN_LINEUP_PLAYERS}/11 historisch bekannt"
        )
        print()

        all_results: dict[
            float,
            list[tuple[int, int, float, float, float]],
        ] = {
            weight: []
            for weight in LINEUP_WEIGHTS
        }

        for (
            competition_id,
            competition_name,
            start_matchday,
            end_matchday,
        ) in COMPETITIONS:
            print("=" * 112)
            print(
                f"{competition_name} "
                f"(ID {competition_id}, ST "
                f"{start_matchday}–{end_matchday})"
            )
            print("=" * 112)

            baseline_matches = None

            for lineup_weight in LINEUP_WEIGHTS:
                service = BacktestService(
                    connection=connection,
                    form_weight=FORM_WEIGHT,
                    form_matches=FORM_MATCHES,
                    opponent_strength_weight=(
                        OPPONENT_STRENGTH_WEIGHT
                    ),
                    player_strength_weight=(
                        PLAYER_STRENGTH_WEIGHT
                    ),
                    lineup_strength_weight=lineup_weight,
                    minimum_lineup_players=(
                        MINIMUM_LINEUP_PLAYERS
                    ),
                    minimum_known_lineup_players=(
                        MINIMUM_KNOWN_LINEUP_PLAYERS
                    ),
                )

                summary = service.run(
                    competition_id=competition_id,
                    start_matchday=start_matchday,
                    end_matchday=end_matchday,
                )

                if lineup_weight == 0.0:
                    baseline_matches = summary.matches_tested
                    mode = "PREMATCH"
                else:
                    mode = "LINEUP"

                coverage = (
                    (
                        summary.matches_tested
                        / baseline_matches
                        * 100.0
                    )
                    if baseline_matches
                    else 0.0
                )

                all_results[lineup_weight].append(
                    (
                        summary.matches_tested,
                        summary.correct_outcomes,
                        summary.accuracy,
                        summary.average_brier_score,
                        summary.average_log_loss,
                    )
                )

                print(
                    f"{mode:<8} "
                    f"{lineup_weight:>4.2f} | "
                    f"{summary.correct_outcomes:>3}/"
                    f"{summary.matches_tested:<3} | "
                    f"{summary.accuracy * 100:>6.2f}% | "
                    f"Brier {summary.average_brier_score:.5f} | "
                    f"LogLoss {summary.average_log_loss:.5f} | "
                    f"Coverage {coverage:>6.2f}%"
                )

            print()

        print("=" * 112)
        print("GESAMT – ALLE WETTBEWERBE")
        print("=" * 112)

        aggregate_results = []

        for lineup_weight in LINEUP_WEIGHTS:
            rows = all_results[lineup_weight]

            total_matches = sum(row[0] for row in rows)
            total_correct = sum(row[1] for row in rows)

            if total_matches <= 0:
                accuracy = 0.0
                brier = 0.0
                log_loss = 0.0
            else:
                accuracy = total_correct / total_matches
                brier = sum(
                    row[3] * row[0]
                    for row in rows
                ) / total_matches
                log_loss = sum(
                    row[4] * row[0]
                    for row in rows
                ) / total_matches

            aggregate_results.append(
                (
                    lineup_weight,
                    total_matches,
                    total_correct,
                    accuracy,
                    brier,
                    log_loss,
                )
            )

            mode = (
                "PREMATCH"
                if lineup_weight == 0.0
                else "LINEUP"
            )

            print(
                f"{mode:<8} "
                f"{lineup_weight:>4.2f} | "
                f"{total_correct:>4}/"
                f"{total_matches:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {brier:.5f} | "
                f"LogLoss {log_loss:.5f}"
            )

        baseline = aggregate_results[0]

        print()
        print("=" * 112)
        print("DELTA GEGEN PREMATCH – GESAMT")
        print("=" * 112)

        for result in aggregate_results[1:]:
            weight, matches, _, accuracy, brier, log_loss = result

            print(
                f"Lineup {weight:>4.2f} | "
                f"Δ Treffer "
                f"{(accuracy - baseline[3]) * 100:+.2f} PP | "
                f"Δ Brier {brier - baseline[4]:+.6f} | "
                f"Δ LogLoss {log_loss - baseline[5]:+.6f} | "
                f"N={matches}"
            )

        comparable = [
            row
            for row in aggregate_results[1:]
            if row[1] > 0
        ]

        if comparable:
            best_brier = min(
                comparable,
                key=lambda row: row[4],
            )
            best_log_loss = min(
                comparable,
                key=lambda row: row[5],
            )
            best_accuracy = max(
                comparable,
                key=lambda row: row[3],
            )

            print()
            print("=" * 112)
            print("BESTE LINEUP-WERTE – GESAMT")
            print("=" * 112)
            print(
                f"Brier:        Gewicht {best_brier[0]:.2f} | "
                f"{best_brier[4]:.5f}"
            )
            print(
                f"LogLoss:      Gewicht {best_log_loss[0]:.2f} | "
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
