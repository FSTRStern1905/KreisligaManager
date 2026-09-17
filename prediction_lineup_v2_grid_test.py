from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService


DATABASE_PATH = Path("data/database/kreisligamanager.db")

COMPETITIONS = (
    (2, "Bundesliga", 5, 34),
    (3, "Regionalliga Südwest", 5, 34),
    (1, "Kreisliga A7", 5, 26),
)

LINEUP_WEIGHTS = (
    0.00,
    0.10,
    0.25,
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
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


def flatten(summary):
    return {
        match.prediction.match_id: match
        for matchday in summary.matchdays
        for match in matchday.matches
    }


def metrics(matches):
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
        "brier": (
            sum(match.brier_score for match in matches)
            / len(matches)
        ),
        "log_loss": (
            sum(match.log_loss for match in matches)
            / len(matches)
        ),
    }


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 112)
        print("LINEUP v2 – GRID-TEST MIT ZENTRIERTEM / SKALIERTEM FAKTOR")
        print("=" * 112)
        print(
            "Gewichte: "
            + " / ".join(
                f"{weight:.2f}"
                for weight in LINEUP_WEIGHTS
            )
        )
        print(
            f"Form {FORM_MATCHES}/{FORM_WEIGHT:.2f} | "
            f"Opponent {OPPONENT_STRENGTH_WEIGHT:.2f} | "
            f"Player {PLAYER_STRENGTH_WEIGHT:.2f}"
        )
        print()

        aggregate = {
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
            print(competition_name)
            print("=" * 112)

            by_weight = {}

            for weight in LINEUP_WEIGHTS:
                summary = run_backtest(
                    connection=connection,
                    competition_id=competition_id,
                    start_matchday=start_matchday,
                    end_matchday=end_matchday,
                    lineup_weight=weight,
                )
                by_weight[weight] = flatten(summary)

            comparable_ids = set(
                by_weight[LINEUP_WEIGHTS[0]]
            )

            for weight in LINEUP_WEIGHTS[1:]:
                comparable_ids &= set(
                    by_weight[weight]
                )

            comparable_ids = sorted(comparable_ids)

            print(
                f"Identische Vergleichsspiele: "
                f"{len(comparable_ids)}"
            )
            print()

            for weight in LINEUP_WEIGHTS:
                selected = [
                    by_weight[weight][match_id]
                    for match_id in comparable_ids
                ]

                aggregate[weight].extend(selected)

                result = metrics(selected)

                mode = (
                    "PREMATCH"
                    if weight == 0.0
                    else "LINEUP"
                )

                print(
                    f"{mode:<8} {weight:>4.2f} | "
                    f"{result['correct']:>3}/"
                    f"{result['matches']:<3} | "
                    f"{result['accuracy'] * 100:>6.2f}% | "
                    f"Brier {result['brier']:.6f} | "
                    f"LogLoss {result['log_loss']:.6f}"
                )

            print()

        print("=" * 112)
        print("GESAMT – IDENTISCHE 694-SPIELE-STICHPROBE")
        print("=" * 112)

        final = {}

        for weight in LINEUP_WEIGHTS:
            result = metrics(aggregate[weight])
            final[weight] = result

            mode = (
                "PREMATCH"
                if weight == 0.0
                else "LINEUP"
            )

            print(
                f"{mode:<8} {weight:>4.2f} | "
                f"{result['correct']:>4}/"
                f"{result['matches']:<4} | "
                f"{result['accuracy'] * 100:>6.2f}% | "
                f"Brier {result['brier']:.6f} | "
                f"LogLoss {result['log_loss']:.6f}"
            )

        baseline = final[0.0]

        print()
        print("=" * 112)
        print("DELTA GEGEN PREMATCH")
        print("=" * 112)

        for weight in LINEUP_WEIGHTS[1:]:
            result = final[weight]

            print(
                f"Lineup {weight:>4.2f} | "
                f"Δ Treffer "
                f"{(result['accuracy'] - baseline['accuracy']) * 100:+.2f} PP | "
                f"Δ Brier "
                f"{result['brier'] - baseline['brier']:+.6f} | "
                f"Δ LogLoss "
                f"{result['log_loss'] - baseline['log_loss']:+.6f}"
            )

        candidates = LINEUP_WEIGHTS[1:]

        best_brier = min(
            candidates,
            key=lambda weight: final[weight]["brier"],
        )
        best_log_loss = min(
            candidates,
            key=lambda weight: final[weight]["log_loss"],
        )
        best_accuracy = max(
            candidates,
            key=lambda weight: final[weight]["accuracy"],
        )

        print()
        print("=" * 112)
        print("OPTIMA IM LINEUP-v2-GRID")
        print("=" * 112)
        print(
            f"Brier:        Gewicht {best_brier:.2f} | "
            f"{final[best_brier]['brier']:.6f}"
        )
        print(
            f"LogLoss:      Gewicht {best_log_loss:.2f} | "
            f"{final[best_log_loss]['log_loss']:.6f}"
        )
        print(
            f"Trefferquote: Gewicht {best_accuracy:.2f} | "
            f"{final[best_accuracy]['accuracy'] * 100:.2f}% "
            f"({final[best_accuracy]['correct']}/"
            f"{final[best_accuracy]['matches']})"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
