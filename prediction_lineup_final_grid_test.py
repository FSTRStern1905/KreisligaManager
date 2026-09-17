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
    0.0,
    2.0,
    3.0,
    4.0,
    5.0,
    6.0,
    8.0,
    10.0,
)

FORM_MATCHES = 6
FORM_WEIGHT = 0.20
OPPONENT_STRENGTH_WEIGHT = 1.25
PLAYER_STRENGTH_WEIGHT = 0.0

MINIMUM_LINEUP_PLAYERS = 11
MINIMUM_KNOWN_LINEUP_PLAYERS = 8


def run_backtest(
    connection,
    competition_id,
    start_matchday,
    end_matchday,
    lineup_weight,
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
        return 0, 0, 0.0, 0.0, 0.0

    correct = sum(
        match.outcome_correct
        for match in matches
    )

    return (
        len(matches),
        correct,
        correct / len(matches),
        sum(match.brier_score for match in matches)
        / len(matches),
        sum(match.log_loss for match in matches)
        / len(matches),
    )


def main():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 110)
        print("FINALER LINEUP-GRID-TEST – IDENTISCHE SPIELE")
        print("=" * 110)
        print(
            "Gewichte: "
            + " / ".join(
                f"{weight:g}"
                for weight in LINEUP_WEIGHTS
            )
        )
        print()

        aggregate = {
            weight: []
            for weight in LINEUP_WEIGHTS
        }

        for (
            competition_id,
            name,
            start_matchday,
            end_matchday,
        ) in COMPETITIONS:
            print("=" * 110)
            print(name)
            print("=" * 110)

            summaries = {}
            by_weight = {}

            for weight in LINEUP_WEIGHTS:
                summary = run_backtest(
                    connection,
                    competition_id,
                    start_matchday,
                    end_matchday,
                    weight,
                )
                summaries[weight] = summary
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

                (
                    count,
                    correct,
                    accuracy,
                    brier,
                    log_loss,
                ) = metrics(selected)

                mode = (
                    "PREMATCH"
                    if weight == 0.0
                    else "LINEUP"
                )

                print(
                    f"{mode:<8} {weight:>5.2f} | "
                    f"{correct:>3}/{count:<3} | "
                    f"{accuracy * 100:>6.2f}% | "
                    f"Brier {brier:.6f} | "
                    f"LogLoss {log_loss:.6f}"
                )

            print()

        print("=" * 110)
        print("GESAMT – IDENTISCHE STICHPROBE")
        print("=" * 110)

        final = {}

        for weight in LINEUP_WEIGHTS:
            result = metrics(aggregate[weight])
            final[weight] = result

            count, correct, accuracy, brier, log_loss = result

            mode = (
                "PREMATCH"
                if weight == 0.0
                else "LINEUP"
            )

            print(
                f"{mode:<8} {weight:>5.2f} | "
                f"{correct:>4}/{count:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {brier:.6f} | "
                f"LogLoss {log_loss:.6f}"
            )

        baseline = final[0.0]

        print()
        print("=" * 110)
        print("DELTA GEGEN PREMATCH")
        print("=" * 110)

        for weight in LINEUP_WEIGHTS[1:]:
            result = final[weight]

            print(
                f"Lineup {weight:>5.2f} | "
                f"Δ Treffer "
                f"{(result[2] - baseline[2]) * 100:+.2f} PP | "
                f"Δ Brier {result[3] - baseline[3]:+.6f} | "
                f"Δ LogLoss {result[4] - baseline[4]:+.6f}"
            )

        candidates = LINEUP_WEIGHTS[1:]

        best_brier = min(
            candidates,
            key=lambda weight: final[weight][3],
        )
        best_log_loss = min(
            candidates,
            key=lambda weight: final[weight][4],
        )
        best_accuracy = max(
            candidates,
            key=lambda weight: final[weight][2],
        )

        print()
        print("=" * 110)
        print("OPTIMA IM FINALEN GRID")
        print("=" * 110)
        print(
            f"Brier:        {best_brier:.2f} "
            f"({final[best_brier][3]:.6f})"
        )
        print(
            f"LogLoss:      {best_log_loss:.2f} "
            f"({final[best_log_loss][4]:.6f})"
        )
        print(
            f"Trefferquote: {best_accuracy:.2f} "
            f"({final[best_accuracy][2] * 100:.2f}%)"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
