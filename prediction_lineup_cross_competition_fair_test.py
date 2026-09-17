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


def run_backtest(
    connection: sqlite3.Connection,
    competition_id: int,
    start_matchday: int,
    end_matchday: int,
    lineup_weight: float,
):
    service = BacktestService(
        connection=connection,
        form_weight=FORM_WEIGHT,
        form_matches=FORM_MATCHES,
        opponent_strength_weight=OPPONENT_STRENGTH_WEIGHT,
        player_strength_weight=PLAYER_STRENGTH_WEIGHT,
        lineup_strength_weight=lineup_weight,
        minimum_lineup_players=MINIMUM_LINEUP_PLAYERS,
        minimum_known_lineup_players=MINIMUM_KNOWN_LINEUP_PLAYERS,
    )

    return service.run(
        competition_id=competition_id,
        start_matchday=start_matchday,
        end_matchday=end_matchday,
    )


def flatten_results(summary):
    return {
        match.prediction.match_id: match
        for matchday in summary.matchdays
        for match in matchday.matches
    }


def calculate_metrics(matches):
    matches = list(matches)

    if not matches:
        return {
            "matches": 0,
            "correct": 0,
            "accuracy": 0.0,
            "brier": 0.0,
            "log_loss": 0.0,
        }

    correct = sum(
        1
        for match in matches
        if match.outcome_correct
    )

    return {
        "matches": len(matches),
        "correct": correct,
        "accuracy": correct / len(matches),
        "brier": sum(
            match.brier_score
            for match in matches
        ) / len(matches),
        "log_loss": sum(
            match.log_loss
            for match in matches
        ) / len(matches),
    }


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 118)
        print("LINEUP CROSS-COMPETITION – FAIRER MATCH-BY-MATCH VERGLEICH")
        print("=" * 118)
        print(
            f"Form {FORM_MATCHES}/{FORM_WEIGHT:.2f} | "
            f"Opponent {OPPONENT_STRENGTH_WEIGHT:.2f} | "
            f"Player {PLAYER_STRENGTH_WEIGHT:.2f} | "
            f"Lineup mindestens "
            f"{MINIMUM_LINEUP_PLAYERS}/11, "
            f"davon {MINIMUM_KNOWN_LINEUP_PLAYERS}/11 bekannt"
        )
        print()

        aggregate = {
            weight: []
            for weight in LINEUP_WEIGHTS
        }

        competitions_used = []
        competitions_without_lineups = []

        for (
            competition_id,
            competition_name,
            start_matchday,
            end_matchday,
        ) in COMPETITIONS:
            print("=" * 118)
            print(
                f"{competition_name} "
                f"(ID {competition_id}, ST "
                f"{start_matchday}–{end_matchday})"
            )
            print("=" * 118)

            prematch_summary = run_backtest(
                connection=connection,
                competition_id=competition_id,
                start_matchday=start_matchday,
                end_matchday=end_matchday,
                lineup_weight=0.0,
            )
            prematch_by_id = flatten_results(
                prematch_summary
            )

            reference_lineup_summary = run_backtest(
                connection=connection,
                competition_id=competition_id,
                start_matchday=start_matchday,
                end_matchday=end_matchday,
                lineup_weight=1.0,
            )
            reference_lineup_by_id = flatten_results(
                reference_lineup_summary
            )

            comparable_ids = sorted(
                set(prematch_by_id)
                & set(reference_lineup_by_id)
            )

            total_prematch = len(prematch_by_id)
            comparable_count = len(comparable_ids)

            coverage = (
                comparable_count / total_prematch * 100.0
                if total_prematch
                else 0.0
            )

            print(
                f"PREMATCH-Spiele insgesamt: {total_prematch}"
            )
            print(
                f"LINEUP-vergleichbar:       "
                f"{comparable_count}/{total_prematch} "
                f"({coverage:.2f}%)"
            )

            if not comparable_ids:
                competitions_without_lineups.append(
                    competition_name
                )
                print(
                    "STATUS: keine ausreichend vollständigen "
                    "LINEUP-Daten – nicht im Gesamtvergleich."
                )
                print()
                continue

            competitions_used.append(competition_name)

            prematch_metrics = calculate_metrics(
                prematch_by_id[match_id]
                for match_id in comparable_ids
            )

            aggregate[0.0].extend(
                prematch_by_id[match_id]
                for match_id in comparable_ids
            )

            print()
            print(
                f"PREMATCH 0.00 | "
                f"{prematch_metrics['correct']:>3}/"
                f"{prematch_metrics['matches']:<3} | "
                f"{prematch_metrics['accuracy'] * 100:>6.2f}% | "
                f"Brier {prematch_metrics['brier']:.5f} | "
                f"LogLoss {prematch_metrics['log_loss']:.5f}"
            )

            for lineup_weight in LINEUP_WEIGHTS[1:]:
                if lineup_weight == 1.0:
                    lineup_summary = reference_lineup_summary
                else:
                    lineup_summary = run_backtest(
                        connection=connection,
                        competition_id=competition_id,
                        start_matchday=start_matchday,
                        end_matchday=end_matchday,
                        lineup_weight=lineup_weight,
                    )

                lineup_by_id = flatten_results(
                    lineup_summary
                )

                missing_ids = [
                    match_id
                    for match_id in comparable_ids
                    if match_id not in lineup_by_id
                ]

                if missing_ids:
                    raise RuntimeError(
                        f"Gewicht {lineup_weight:.2f}: "
                        f"{len(missing_ids)} Vergleichsspiele "
                        "fehlen unerwartet."
                    )

                lineup_matches = [
                    lineup_by_id[match_id]
                    for match_id in comparable_ids
                ]

                metrics = calculate_metrics(
                    lineup_matches
                )

                aggregate[lineup_weight].extend(
                    lineup_matches
                )

                print(
                    f"LINEUP   {lineup_weight:>4.2f} | "
                    f"{metrics['correct']:>3}/"
                    f"{metrics['matches']:<3} | "
                    f"{metrics['accuracy'] * 100:>6.2f}% | "
                    f"Brier {metrics['brier']:.5f} | "
                    f"LogLoss {metrics['log_loss']:.5f}"
                )

            print()

        print("=" * 118)
        print("FAIRER GESAMTVERGLEICH – NUR IDENTISCHE SPIELE")
        print("=" * 118)

        aggregate_metrics = {}

        for lineup_weight in LINEUP_WEIGHTS:
            metrics = calculate_metrics(
                aggregate[lineup_weight]
            )
            aggregate_metrics[lineup_weight] = metrics

            mode = (
                "PREMATCH"
                if lineup_weight == 0.0
                else "LINEUP"
            )

            print(
                f"{mode:<8} "
                f"{lineup_weight:>4.2f} | "
                f"{metrics['correct']:>4}/"
                f"{metrics['matches']:<4} | "
                f"{metrics['accuracy'] * 100:>6.2f}% | "
                f"Brier {metrics['brier']:.5f} | "
                f"LogLoss {metrics['log_loss']:.5f}"
            )

        baseline = aggregate_metrics[0.0]

        print()
        print("=" * 118)
        print("DELTA GEGEN PREMATCH – IDENTISCHE STICHPROBE")
        print("=" * 118)

        for lineup_weight in LINEUP_WEIGHTS[1:]:
            metrics = aggregate_metrics[lineup_weight]

            print(
                f"Lineup {lineup_weight:>4.2f} | "
                f"Δ Treffer "
                f"{(metrics['accuracy'] - baseline['accuracy']) * 100:+.2f} PP | "
                f"Δ Brier "
                f"{metrics['brier'] - baseline['brier']:+.6f} | "
                f"Δ LogLoss "
                f"{metrics['log_loss'] - baseline['log_loss']:+.6f} | "
                f"N={metrics['matches']}"
            )

        comparable_weights = LINEUP_WEIGHTS[1:]

        best_brier_weight = min(
            comparable_weights,
            key=lambda weight: (
                aggregate_metrics[weight]["brier"]
            ),
        )
        best_log_loss_weight = min(
            comparable_weights,
            key=lambda weight: (
                aggregate_metrics[weight]["log_loss"]
            ),
        )
        best_accuracy_weight = max(
            comparable_weights,
            key=lambda weight: (
                aggregate_metrics[weight]["accuracy"]
            ),
        )

        print()
        print("=" * 118)
        print("BESTE LINEUP-WERTE – IDENTISCHE STICHPROBE")
        print("=" * 118)
        print(
            f"Brier:        Gewicht {best_brier_weight:.2f} | "
            f"{aggregate_metrics[best_brier_weight]['brier']:.5f}"
        )
        print(
            f"LogLoss:      Gewicht {best_log_loss_weight:.2f} | "
            f"{aggregate_metrics[best_log_loss_weight]['log_loss']:.5f}"
        )
        print(
            f"Trefferquote: Gewicht {best_accuracy_weight:.2f} | "
            f"{aggregate_metrics[best_accuracy_weight]['accuracy'] * 100:.2f}% "
            f"("
            f"{aggregate_metrics[best_accuracy_weight]['correct']}/"
            f"{aggregate_metrics[best_accuracy_weight]['matches']}"
            f")"
        )

        print()
        print("Im Gesamtvergleich enthalten:")
        for name in competitions_used:
            print(f"  + {name}")

        if competitions_without_lineups:
            print("Nicht enthalten – keine ausreichenden LINEUP-Daten:")
            for name in competitions_without_lineups:
                print(f"  - {name}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
