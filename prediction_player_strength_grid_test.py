from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.form_service import FormService
from src.services.prediction.team_strength_service import (
    TeamStrengthService,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")

START_MATCHDAY = 5
MIN_FINISHED_MATCHES = 80
MIN_MATCHDAYS = 10

STRENGTH_SMOOTHING = 5.0
FORM_MATCHES = 6
FORM_WEIGHT = 0.20
RECENCY_OLDEST_WEIGHT = 0.10
OPPONENT_STRENGTH_WEIGHT = 1.25
PLAYER_CORE_SIZE = 14

PLAYER_STRENGTH_WEIGHTS = (
    0.00,
    0.25,
    0.50,
    0.75,
    1.00,
    1.50,
    2.00,
)


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    old_smoothing = TeamStrengthService.SMOOTHING_MATCHES
    old_recency = FormService.OLDEST_WEIGHT

    TeamStrengthService.SMOOTHING_MATCHES = (
        STRENGTH_SMOOTHING
    )
    FormService.OLDEST_WEIGHT = RECENCY_OLDEST_WEIGHT

    try:
        competitions = _get_competitions(connection)

        print("=" * 105)
        print("PLAYER STRENGTH GRID TEST")
        print("=" * 105)
        print(
            f"Reale Wettbewerbe:       {len(competitions)}"
        )
        print(
            f"Start-Spieltag:          {START_MATCHDAY}"
        )
        print(
            f"Strength-Smoothing:      {STRENGTH_SMOOTHING}"
        )
        print(
            f"Form:                    "
            f"{FORM_MATCHES} Spiele / {FORM_WEIGHT:.2f}"
        )
        print(
            f"Recency oldest weight:   "
            f"{RECENCY_OLDEST_WEIGHT:.2f}"
        )
        print(
            f"Opponent Strength:       "
            f"{OPPONENT_STRENGTH_WEIGHT:.2f}"
        )
        print(
            f"Player Core Size:        {PLAYER_CORE_SIZE}"
        )
        print()

        aggregate = []

        for player_weight in PLAYER_STRENGTH_WEIGHTS:
            total_matches = 0
            total_correct = 0
            weighted_brier = 0.0
            weighted_log_loss = 0.0

            print("-" * 105)
            print(
                f"PLAYER STRENGTH WEIGHT "
                f"{player_weight:.2f}"
            )
            print("-" * 105)

            for competition in competitions:
                service = BacktestService(
                    connection=connection,
                    form_weight=FORM_WEIGHT,
                    form_matches=FORM_MATCHES,
                    opponent_strength_weight=(
                        OPPONENT_STRENGTH_WEIGHT
                    ),
                    player_strength_weight=player_weight,
                    player_core_size=PLAYER_CORE_SIZE,
                )

                summary = service.run(
                    competition_id=competition["competition_id"],
                    start_matchday=START_MATCHDAY,
                )

                matches = summary.matches_tested
                correct = summary.correct_outcomes

                total_matches += matches
                total_correct += correct
                weighted_brier += (
                    summary.average_brier_score * matches
                )
                weighted_log_loss += (
                    summary.average_log_loss * matches
                )

                print(
                    f"{competition['name'][:42]:<42} | "
                    f"{correct:>3}/{matches:<3} | "
                    f"{summary.accuracy * 100:>6.2f}% | "
                    f"Brier {summary.average_brier_score:.4f} | "
                    f"LogLoss {summary.average_log_loss:.4f}"
                )

            average_brier = (
                weighted_brier / total_matches
                if total_matches
                else 0.0
            )
            average_log_loss = (
                weighted_log_loss / total_matches
                if total_matches
                else 0.0
            )
            accuracy = (
                total_correct / total_matches
                if total_matches
                else 0.0
            )

            aggregate.append(
                (
                    player_weight,
                    total_correct,
                    total_matches,
                    accuracy,
                    average_brier,
                    average_log_loss,
                )
            )

            print(
                f"GESAMT                                     | "
                f"{total_correct:>3}/{total_matches:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {average_brier:.4f} | "
                f"LogLoss {average_log_loss:.4f}"
            )

        print()
        print("=" * 105)
        print("AGGREGATE")
        print("=" * 105)

        for (
            player_weight,
            correct,
            matches,
            accuracy,
            brier,
            log_loss,
        ) in aggregate:
            print(
                f"Player {player_weight:>4.2f} | "
                f"{correct:>3}/{matches:<4} | "
                f"{accuracy * 100:>6.2f}% | "
                f"Brier {brier:.4f} | "
                f"LogLoss {log_loss:.4f}"
            )

    finally:
        TeamStrengthService.SMOOTHING_MATCHES = (
            old_smoothing
        )
        FormService.OLDEST_WEIGHT = old_recency
        connection.close()


def _get_competitions(
    connection: sqlite3.Connection,
) -> list[dict]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            competitions.competition_id,
            competitions.name,
            COUNT(matches.match_id) AS finished_matches,
            COUNT(DISTINCT matches.matchday) AS matchdays
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
            AND COUNT(DISTINCT matches.matchday) >= ?
        ORDER BY
            COUNT(matches.match_id) DESC,
            competitions.competition_id;
        """,
        (
            MIN_FINISHED_MATCHES,
            MIN_MATCHDAYS,
        ),
    )

    return [
        dict(row)
        for row in cursor.fetchall()
    ]


if __name__ == "__main__":
    main()
