from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.prediction.backtest_service import (
    BacktestService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

# Aktuell ausreichend vollständige echte Wettbewerbe.
COMPETITION_IDS = (
    175,  # Oberliga Rheinland-Pfalz/Saar 2023/24
    2,    # Bundesliga 2025/26
    3,    # Regionalliga Südwest 2025/26
    1,    # Kreisliga A7 2025/26
)

FORM_MATCHES = 6
FORM_WEIGHT = 0.20

OPPONENT_STRENGTH_WEIGHT = 1.25

PLAYER_STRENGTH_WEIGHT = 0.0

# PREMATCH:
# tatsächliche Startelf des Zielspiels darf
# NICHT verwendet werden.
LINEUP_STRENGTH_WEIGHT = 0.0


@dataclass
class AggregateResult:
    matches: int = 0
    correct: int = 0
    brier_sum: float = 0.0
    log_loss_sum: float = 0.0

    def add_match(
        self,
        match,
    ) -> None:
        self.matches += 1

        if match.outcome_correct:
            self.correct += 1

        self.brier_sum += (
            match.brier_score
        )

        self.log_loss_sum += (
            match.log_loss
        )

    @property
    def accuracy(self) -> float:
        if self.matches <= 0:
            return 0.0

        return (
            self.correct
            / self.matches
        )

    @property
    def brier(self) -> float:
        if self.matches <= 0:
            return 0.0

        return (
            self.brier_sum
            / self.matches
        )

    @property
    def log_loss(self) -> float:
        if self.matches <= 0:
            return 0.0

        return (
            self.log_loss_sum
            / self.matches
        )


def competition_name(
    connection: sqlite3.Connection,
    competition_id: int,
) -> str:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM competitions
        WHERE competition_id = ?;
        """,
        (
            competition_id,
        ),
    )

    row = cursor.fetchone()

    if (
        row is None
        or not row[0]
    ):
        return (
            f"Competition {competition_id}"
        )

    return str(
        row[0]
    )


def create_backtest_service(
    connection: sqlite3.Connection,
) -> BacktestService:
    return BacktestService(
        connection=connection,
        form_weight=FORM_WEIGHT,
        form_matches=FORM_MATCHES,
        opponent_strength_weight=(
            OPPONENT_STRENGTH_WEIGHT
        ),
        player_strength_weight=(
            PLAYER_STRENGTH_WEIGHT
        ),
        lineup_strength_weight=(
            LINEUP_STRENGTH_WEIGHT
        ),
    )


def print_matchday_table(
    results: dict[int, AggregateResult],
) -> None:
    print()
    print("=" * 86)
    print("ERGEBNIS NACH PROGNOSE-SPIELTAG")
    print("=" * 86)

    print(
        f"{'ST':>4}"
        f"{'Spiele':>10}"
        f"{'Treffer':>10}"
        f"{'Quote':>12}"
        f"{'Brier':>14}"
        f"{'LogLoss':>14}"
    )

    print("-" * 86)

    for matchday in sorted(
        results
    ):
        result = results[
            matchday
        ]

        print(
            f"{matchday:>4}"
            f"{result.matches:>10}"
            f"{result.correct:>10}"
            f"{result.accuracy * 100:>11.2f}%"
            f"{result.brier:>14.4f}"
            f"{result.log_loss:>14.4f}"
        )


def aggregate_range(
    results: dict[int, AggregateResult],
    start_matchday: int,
    end_matchday: int | None,
) -> AggregateResult:
    aggregate = AggregateResult()

    for matchday, result in (
        results.items()
    ):
        if matchday < start_matchday:
            continue

        if (
            end_matchday is not None
            and matchday > end_matchday
        ):
            continue

        aggregate.matches += (
            result.matches
        )

        aggregate.correct += (
            result.correct
        )

        aggregate.brier_sum += (
            result.brier_sum
        )

        aggregate.log_loss_sum += (
            result.log_loss_sum
        )

    return aggregate


def print_phase(
    name: str,
    result: AggregateResult,
) -> None:
    print(
        f"{name:<22}"
        f"{result.matches:>8}"
        f"{result.correct:>10}"
        f"{result.accuracy * 100:>11.2f}%"
        f"{result.brier:>14.4f}"
        f"{result.log_loss:>14.4f}"
    )


def print_phase_table(
    results: dict[int, AggregateResult],
) -> None:
    print()
    print("=" * 86)
    print("SAISONPHASEN")
    print("=" * 86)

    print(
        f"{'Phase':<22}"
        f"{'Spiele':>8}"
        f"{'Treffer':>10}"
        f"{'Quote':>12}"
        f"{'Brier':>14}"
        f"{'LogLoss':>14}"
    )

    print("-" * 86)

    print_phase(
        "Frühphase ST 2–4",
        aggregate_range(
            results,
            2,
            4,
        ),
    )

    print_phase(
        "Übergang ST 5–7",
        aggregate_range(
            results,
            5,
            7,
        ),
    )

    print_phase(
        "Stabil ST 8+",
        aggregate_range(
            results,
            8,
            None,
        ),
    )


def print_cumulative_table(
    results: dict[int, AggregateResult],
) -> None:
    print()
    print("=" * 86)
    print("KUMULATIVE FRÜHPHASE")
    print("=" * 86)

    print(
        f"{'Datenstand':<22}"
        f"{'Spiele':>8}"
        f"{'Treffer':>10}"
        f"{'Quote':>12}"
        f"{'Brier':>14}"
        f"{'LogLoss':>14}"
    )

    print("-" * 86)

    for end_matchday in range(
        2,
        11,
    ):
        result = aggregate_range(
            results,
            2,
            end_matchday,
        )

        print(
            f"{f'ST 2–{end_matchday}':<22}"
            f"{result.matches:>8}"
            f"{result.correct:>10}"
            f"{result.accuracy * 100:>11.2f}%"
            f"{result.brier:>14.4f}"
            f"{result.log_loss:>14.4f}"
        )


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: "
            f"{DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        matchday_results: dict[
            int,
            AggregateResult,
        ] = defaultdict(
            AggregateResult
        )

        print()
        print("=" * 86)
        print("EARLY-SEASON BACKTEST")
        print("=" * 86)

        print(
            f"Form: {FORM_MATCHES} Spiele | "
            f"Gewicht {FORM_WEIGHT:.2f}"
        )

        print(
            "Opponent Strength: "
            f"{OPPONENT_STRENGTH_WEIGHT:.2f}"
        )

        print(
            "Player Strength: "
            f"{PLAYER_STRENGTH_WEIGHT:.2f}"
        )

        print(
            "Lineup Strength: "
            f"{LINEUP_STRENGTH_WEIGHT:.2f} "
            "(PREMATCH)"
        )

        print()

        for competition_id in (
            COMPETITION_IDS
        ):
            name = competition_name(
                connection,
                competition_id,
            )

            print(
                f"Teste ID {competition_id}: "
                f"{name}"
            )

            service = (
                create_backtest_service(
                    connection
                )
            )

            try:
                summary = service.run(
                    competition_id=(
                        competition_id
                    ),
                    start_matchday=2,
                )

            except Exception as exc:
                print(
                    f"  FEHLER: {exc}"
                )

                continue

            print(
                f"  {summary.matches_tested} "
                "Prognosen"
            )

            for matchday_result in (
                summary.matchdays
            ):
                aggregate = (
                    matchday_results[
                        matchday_result.matchday
                    ]
                )

                for match in (
                    matchday_result.matches
                ):
                    aggregate.add_match(
                        match
                    )

        if not matchday_results:
            raise RuntimeError(
                "Keine Backtest-Ergebnisse "
                "vorhanden."
            )

        print_matchday_table(
            matchday_results
        )

        print_phase_table(
            matchday_results
        )

        print_cumulative_table(
            matchday_results
        )

        total = aggregate_range(
            matchday_results,
            2,
            None,
        )

        print()
        print("=" * 86)
        print("GESAMT")
        print("=" * 86)

        print(
            f"Prognosen:     "
            f"{total.matches}"
        )

        print(
            f"Treffer:       "
            f"{total.correct}"
        )

        print(
            f"Trefferquote:  "
            f"{total.accuracy * 100:.2f} %"
        )

        print(
            f"Brier:         "
            f"{total.brier:.4f}"
        )

        print(
            f"LogLoss:       "
            f"{total.log_loss:.4f}"
        )

        print("=" * 86)

    finally:
        connection.close()


if __name__ == "__main__":
    main()