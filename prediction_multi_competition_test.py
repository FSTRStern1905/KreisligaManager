from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.services.prediction.backtest_service import BacktestService
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")

START_MATCHDAY = 5
MIN_FINISHED_MATCHES = 80
MIN_MATCHDAYS = 10
STRENGTH_SMOOTHING = 5.0

CONFIGURATIONS = (
    ("Baseline", 5, 0.00),
    ("Form 6 / 0.20", 6, 0.20),
    ("Form 10 / 0.20", 10, 0.20),
)


@dataclass(frozen=True, slots=True)
class CompetitionCandidate:
    competition_id: int
    competition_name: str
    season_name: str
    source: str
    finished_matches: int
    first_matchday: int
    last_matchday: int


@dataclass(frozen=True, slots=True)
class TestResult:
    competition: CompetitionCandidate
    configuration_name: str
    matches_tested: int
    correct_outcomes: int
    accuracy: float
    brier: float


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    original_smoothing = TeamStrengthService.SMOOTHING_MATCHES

    try:
        TeamStrengthService.SMOOTHING_MATCHES = STRENGTH_SMOOTHING

        competitions = _find_real_competitions(connection)

        print("=" * 110)
        print("PREDICTION ENGINE – REAL DATA MULTI-COMPETITION BACKTEST")
        print("=" * 110)
        print(f"Strength-Smoothing:   {STRENGTH_SMOOTHING}")
        print(f"Backtest ab:          Spieltag {START_MATCHDAY}")
        print(f"Mindestspiele:        {MIN_FINISHED_MATCHES}")
        print(f"Mindestspieltage:     {MIN_MATCHDAYS}")
        print("Datenfilter:           competitions.source = 'fussball.de'")
        print()

        if not competitions:
            print(
                "Keine ausreichend vollständigen real importierten "
                "Wettbewerbe gefunden."
            )
            print()
            print(
                "Der Test akzeptiert nur Wettbewerbe mit "
                "competitions.source = 'fussball.de'."
            )
            return

        print(f"Echte Wettbewerbe gefunden: {len(competitions)}")
        print()

        for competition in competitions:
            print(
                f"ID {competition.competition_id:>4} | "
                f"{competition.competition_name} | "
                f"{competition.season_name} | "
                f"{competition.finished_matches} Spiele | "
                f"ST {competition.first_matchday}–{competition.last_matchday} | "
                f"Quelle: {competition.source}"
            )

        print()
        print("=" * 110)
        print("BACKTEST")
        print("=" * 110)

        results: list[TestResult] = []

        for competition in competitions:
            print()
            print(
                f"{competition.competition_name} "
                f"({competition.season_name}) "
                f"[ID {competition.competition_id}]"
            )
            print("-" * 110)

            for name, form_matches, form_weight in CONFIGURATIONS:
                service = BacktestService(
                    connection=connection,
                    form_matches=form_matches,
                    form_weight=form_weight,
                )

                summary = service.run(
                    competition_id=competition.competition_id,
                    start_matchday=START_MATCHDAY,
                    end_matchday=competition.last_matchday,
                )

                result = TestResult(
                    competition=competition,
                    configuration_name=name,
                    matches_tested=summary.matches_tested,
                    correct_outcomes=summary.correct_outcomes,
                    accuracy=summary.accuracy,
                    brier=summary.average_brier_score,
                )
                results.append(result)

                print(
                    f"{name:<18} | "
                    f"{result.correct_outcomes:>4}/"
                    f"{result.matches_tested:<4} | "
                    f"{result.accuracy * 100:>6.2f}% | "
                    f"Brier {result.brier:.4f}"
                )

        print()
        print("=" * 110)
        print("VERGLEICH PRO WETTBEWERB")
        print("=" * 110)

        for competition in competitions:
            competition_results = [
                result
                for result in results
                if result.competition.competition_id
                == competition.competition_id
            ]

            baseline = _get_result(
                competition_results,
                "Baseline",
            )

            print()
            print(
                f"{competition.competition_name} "
                f"({competition.season_name}) "
                f"[ID {competition.competition_id}]"
            )

            for result in competition_results:
                accuracy_change = (
                    result.accuracy - baseline.accuracy
                ) * 100

                brier_change = (
                    result.brier - baseline.brier
                )

                print(
                    f"  {result.configuration_name:<18} "
                    f"{result.accuracy * 100:>6.2f}% "
                    f"({accuracy_change:+6.2f} PP) | "
                    f"Brier {result.brier:.4f} "
                    f"({brier_change:+.4f})"
                )

        print()
        print("=" * 110)
        print("GESAMTAUSWERTUNG – NUR REALE WETTBEWERBE")
        print("=" * 110)

        aggregate = []

        for name, _, _ in CONFIGURATIONS:
            configuration_results = [
                result
                for result in results
                if result.configuration_name == name
            ]

            total_matches = sum(
                result.matches_tested
                for result in configuration_results
            )
            total_correct = sum(
                result.correct_outcomes
                for result in configuration_results
            )

            if total_matches == 0:
                continue

            accuracy = total_correct / total_matches

            weighted_brier = sum(
                result.brier * result.matches_tested
                for result in configuration_results
            ) / total_matches

            aggregate.append(
                (
                    name,
                    total_matches,
                    total_correct,
                    accuracy,
                    weighted_brier,
                )
            )

        baseline = next(
            item
            for item in aggregate
            if item[0] == "Baseline"
        )

        for name, matches, correct, accuracy, brier in aggregate:
            print(
                f"{name:<18} | "
                f"{correct:>5}/{matches:<5} | "
                f"{accuracy * 100:>6.2f}% "
                f"({(accuracy - baseline[3]) * 100:+6.2f} PP) | "
                f"Brier {brier:.4f} "
                f"({brier - baseline[4]:+.4f})"
            )

    finally:
        TeamStrengthService.SMOOTHING_MATCHES = original_smoothing
        connection.close()


def _find_real_competitions(
    connection: sqlite3.Connection,
) -> list[CompetitionCandidate]:
    columns = _table_columns(
        connection,
        "competitions",
    )

    if "source" not in columns:
        raise RuntimeError(
            "Die Tabelle competitions besitzt keine source-Spalte. "
            "Bitte zuerst die ImportSchemaMigration ausführen."
        )

    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            competitions.competition_id,
            competitions.name AS competition_name,
            COALESCE(seasons.name, '') AS season_name,
            competitions.source,
            COUNT(matches.match_id) AS finished_matches,
            MIN(matches.matchday) AS first_matchday,
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
            seasons.name,
            competitions.source
        HAVING
            COUNT(matches.match_id) >= ?
            AND (
                MAX(matches.matchday)
                - MIN(matches.matchday)
                + 1
            ) >= ?
        ORDER BY
            finished_matches DESC,
            competitions.competition_id;
        """,
        (
            MIN_FINISHED_MATCHES,
            MIN_MATCHDAYS,
        ),
    )

    return [
        CompetitionCandidate(
            competition_id=int(row["competition_id"]),
            competition_name=str(row["competition_name"]),
            season_name=str(
                row["season_name"] or "Saison unbekannt"
            ),
            source=str(row["source"]),
            finished_matches=int(row["finished_matches"]),
            first_matchday=int(row["first_matchday"]),
            last_matchday=int(row["last_matchday"]),
        )
        for row in cursor.fetchall()
    ]


def _table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    cursor = connection.cursor()
    cursor.execute(
        f"PRAGMA table_info({table_name});"
    )

    return {
        str(row["name"])
        for row in cursor.fetchall()
    }


def _get_result(
    results: list[TestResult],
    name: str,
) -> TestResult:
    for result in results:
        if result.configuration_name == name:
            return result

    raise RuntimeError(
        f"Testergebnis '{name}' nicht gefunden."
    )


if __name__ == "__main__":
    main()
