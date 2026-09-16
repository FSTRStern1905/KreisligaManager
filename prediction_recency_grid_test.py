from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.form_service import FormService
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")

START_MATCHDAY = 5
MIN_FINISHED_MATCHES = 80
MIN_MATCHDAYS = 10

FORM_MATCHES = 6
FORM_WEIGHT = 0.20
STRENGTH_SMOOTHING = 5.0

RECENCY_WEIGHTS = (
    0.20,
    0.10,
    0.05,
    0.02,
    0.00,
)


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    original_strength_smoothing = TeamStrengthService.SMOOTHING_MATCHES
    original_oldest_weight = FormService.OLDEST_WEIGHT

    try:
        TeamStrengthService.SMOOTHING_MATCHES = STRENGTH_SMOOTHING

        competitions = _find_competitions(connection)

        print("=" * 100)
        print("PREDICTION ENGINE – RECENCY WEIGHT GRID TEST")
        print("=" * 100)
        print(f"Echte Wettbewerbe: {len(competitions)}")
        print(f"Formfenster:       {FORM_MATCHES} Spiele")
        print(f"Formgewicht:       {FORM_WEIGHT:.2f}")
        print()

        aggregate_results = []

        for oldest_weight in RECENCY_WEIGHTS:
            FormService.OLDEST_WEIGHT = oldest_weight

            total_matches = 0
            total_correct = 0
            weighted_brier_sum = 0.0

            print(f"Oldest weight: {oldest_weight:.2f}")

            for row in competitions:
                service = BacktestService(
                    connection=connection,
                    form_matches=FORM_MATCHES,
                    form_weight=FORM_WEIGHT,
                )

                summary = service.run(
                    competition_id=int(row["competition_id"]),
                    start_matchday=START_MATCHDAY,
                    end_matchday=int(row["last_matchday"]),
                )

                total_matches += summary.matches_tested
                total_correct += summary.correct_outcomes
                weighted_brier_sum += (
                    summary.average_brier_score
                    * summary.matches_tested
                )

                print(
                    f"  {row['name']:<42} "
                    f"{summary.correct_outcomes:>3}/"
                    f"{summary.matches_tested:<3} | "
                    f"{summary.accuracy * 100:>6.2f}% | "
                    f"Brier {summary.average_brier_score:.4f}"
                )

            accuracy = total_correct / total_matches
            brier = weighted_brier_sum / total_matches

            aggregate_results.append(
                (
                    oldest_weight,
                    total_matches,
                    total_correct,
                    accuracy,
                    brier,
                )
            )

            print(
                f"  GESAMT{'':<36} "
                f"{total_correct:>3}/{total_matches:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {brier:.4f}"
            )
            print()

        print("=" * 100)
        print("GESAMTVERGLEICH")
        print("=" * 100)

        for (
            oldest_weight,
            matches,
            correct,
            accuracy,
            brier,
        ) in aggregate_results:
            print(
                f"{oldest_weight:>4.2f} -> 1.00 | "
                f"{correct:>4}/{matches:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {brier:.4f}"
            )

    finally:
        FormService.OLDEST_WEIGHT = original_oldest_weight
        TeamStrengthService.SMOOTHING_MATCHES = original_strength_smoothing
        connection.close()


def _find_competitions(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            competitions.competition_id,
            competitions.name,
            COUNT(matches.match_id) AS finished_matches,
            MAX(matches.matchday) AS last_matchday
        FROM competitions
        INNER JOIN matches
            ON matches.competition_id = competitions.competition_id
        WHERE
            competitions.source = 'fussball.de'
            AND matches.matchday IS NOT NULL
            AND matches.home_goals IS NOT NULL
            AND matches.away_goals IS NOT NULL
        GROUP BY
            competitions.competition_id,
            competitions.name
        HAVING
            COUNT(matches.match_id) >= ?
            AND (
                MAX(matches.matchday)
                - MIN(matches.matchday)
                + 1
            ) >= ?
        ORDER BY
            competitions.competition_id
        """,
        (
            MIN_FINISHED_MATCHES,
            MIN_MATCHDAYS,
        ),
    )

    return list(cursor.fetchall())


if __name__ == "__main__":
    main()
