from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.form_service import FormService
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")

START_MATCHDAY = 5
MIN_FINISHED_MATCHES = 80
MIN_MATCHDAYS = 10

STRENGTH_SMOOTHING = 5.0
FORM_MATCHES = 6
FORM_WEIGHT = 0.20
RECENCY_OLDEST_WEIGHT = 0.10

OPPONENT_WEIGHTS = (
    1.00,
    1.25,
    1.50,
    1.75,
    2.00,
)


@dataclass(frozen=True, slots=True)
class Competition:
    competition_id: int
    name: str
    season_name: str
    finished_matches: int
    last_matchday: int


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    original_strength_smoothing = TeamStrengthService.SMOOTHING_MATCHES
    original_oldest_weight = FormService.OLDEST_WEIGHT

    try:
        TeamStrengthService.SMOOTHING_MATCHES = STRENGTH_SMOOTHING
        FormService.OLDEST_WEIGHT = RECENCY_OLDEST_WEIGHT

        competitions = _find_competitions(connection)

        print("=" * 110)
        print("PREDICTION ENGINE – OPPONENT STRENGTH GRID BACKTEST")
        print("=" * 110)
        print(f"Echte Wettbewerbe:       {len(competitions)}")
        print(f"Backtest ab:              Spieltag {START_MATCHDAY}")
        print(f"Strength-Smoothing:       {STRENGTH_SMOOTHING}")
        print(f"Formfenster:              {FORM_MATCHES}")
        print(f"Formgewicht:              {FORM_WEIGHT:.2f}")
        print(f"Recency oldest weight:    {RECENCY_OLDEST_WEIGHT:.2f}")
        print()

        aggregate_results: list[
            tuple[float, int, int, float, float]
        ] = []

        for opponent_weight in OPPONENT_WEIGHTS:
            print("=" * 110)
            print(
                "OPPONENT STRENGTH WEIGHT: "
                f"{opponent_weight:.2f}"
            )
            print("=" * 110)

            total_matches = 0
            total_correct = 0
            total_brier = 0.0

            for competition in competitions:
                service = BacktestService(
                    connection=connection,
                    form_matches=FORM_MATCHES,
                    form_weight=FORM_WEIGHT,
                    opponent_strength_weight=opponent_weight,
                )

                summary = service.run(
                    competition_id=competition.competition_id,
                    start_matchday=START_MATCHDAY,
                    end_matchday=competition.last_matchday,
                )

                total_matches += summary.matches_tested
                total_correct += summary.correct_outcomes
                total_brier += (
                    summary.average_brier_score
                    * summary.matches_tested
                )

                print(
                    f"{competition.name:<43} | "
                    f"{summary.correct_outcomes:>3}/"
                    f"{summary.matches_tested:<3} | "
                    f"{summary.accuracy * 100:>6.2f}% | "
                    f"Brier {summary.average_brier_score:.4f}"
                )

            accuracy = (
                total_correct / total_matches
                if total_matches
                else 0.0
            )
            average_brier = (
                total_brier / total_matches
                if total_matches
                else 0.0
            )

            aggregate_results.append(
                (
                    opponent_weight,
                    total_matches,
                    total_correct,
                    accuracy,
                    average_brier,
                )
            )

            print("-" * 110)
            print(
                f"{'GESAMT':<43} | "
                f"{total_correct:>3}/{total_matches:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {average_brier:.4f}"
            )
            print()

        baseline = aggregate_results[0]
        baseline_accuracy = baseline[3]
        baseline_brier = baseline[4]

        print("=" * 110)
        print("GESAMTVERGLEICH")
        print("=" * 110)

        for (
            opponent_weight,
            matches,
            correct,
            accuracy,
            brier,
        ) in aggregate_results:
            accuracy_delta = (
                accuracy - baseline_accuracy
            ) * 100.0
            brier_delta = brier - baseline_brier

            print(
                f"Opponent {opponent_weight:>4.2f} | "
                f"{correct:>4}/{matches:<4} | "
                f"{accuracy * 100:>6.2f}% "
                f"({accuracy_delta:+6.2f} PP) | "
                f"Brier {brier:.4f} "
                f"({brier_delta:+.4f})"
            )

    finally:
        TeamStrengthService.SMOOTHING_MATCHES = (
            original_strength_smoothing
        )
        FormService.OLDEST_WEIGHT = original_oldest_weight
        connection.close()


def _find_competitions(
    connection: sqlite3.Connection,
) -> list[Competition]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            competitions.competition_id,
            competitions.name,
            COALESCE(seasons.name, '') AS season_name,
            COUNT(matches.match_id) AS finished_matches,
            MAX(matches.matchday) AS last_matchday
        FROM competitions
        LEFT JOIN seasons
            ON seasons.season_id = competitions.season_id
        INNER JOIN matches
            ON matches.competition_id = competitions.competition_id
        WHERE
            competitions.source = 'fussball.de'
            AND matches.matchday IS NOT NULL
            AND matches.home_goals IS NOT NULL
            AND matches.away_goals IS NOT NULL
        GROUP BY
            competitions.competition_id,
            competitions.name,
            seasons.name
        HAVING
            COUNT(matches.match_id) >= ?
            AND (
                MAX(matches.matchday)
                - MIN(matches.matchday)
                + 1
            ) >= ?
        ORDER BY
            COUNT(matches.match_id) DESC,
            competitions.competition_id
        """,
        (
            MIN_FINISHED_MATCHES,
            MIN_MATCHDAYS,
        ),
    )

    return [
        Competition(
            competition_id=int(row["competition_id"]),
            name=str(row["name"]),
            season_name=str(row["season_name"]),
            finished_matches=int(row["finished_matches"]),
            last_matchday=int(row["last_matchday"]),
        )
        for row in cursor.fetchall()
    ]


if __name__ == "__main__":
    main()
