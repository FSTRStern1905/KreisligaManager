from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.prediction_service import (
    PredictionMode,
    PredictionService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

COMPETITION_ID = 2
TARGET_MATCHDAY = 10


def find_test_match(
    connection: sqlite3.Connection,
) -> int:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            match_id,
            home_team_id,
            away_team_id
        FROM matches
        WHERE
            competition_id = ?
            AND matchday = ?
        ORDER BY match_id
        LIMIT 1;
        """,
        (
            COMPETITION_ID,
            TARGET_MATCHDAY,
        ),
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "Kein Testspiel gefunden."
        )

    return int(row[0])


def print_prediction(
    title: str,
    prediction,
) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    print(
        f"Spiel:              "
        f"{prediction.home_team_name} - "
        f"{prediction.away_team_name}"
    )

    print(
        f"Match-ID:           "
        f"{prediction.match_id}"
    )

    print(
        f"Wettbewerb-ID:      "
        f"{prediction.competition_id}"
    )

    print(
        f"Cutoff-Spieltag:    "
        f"{prediction.cutoff_matchday}"
    )

    print()
    print("ERWARTETE TORE")
    print("-" * 78)

    print(
        f"Heim:               "
        f"{prediction.expected_home_goals:.3f}"
    )

    print(
        f"Auswärts:           "
        f"{prediction.expected_away_goals:.3f}"
    )

    print()
    print("1 / X / 2")
    print("-" * 78)

    print(
        f"1:                  "
        f"{prediction.home_win_probability * 100:6.2f} %"
    )

    print(
        f"X:                  "
        f"{prediction.draw_probability * 100:6.2f} %"
    )

    print(
        f"2:                  "
        f"{prediction.away_win_probability * 100:6.2f} %"
    )

    print(
        f"Prognose:           "
        f"{prediction.predicted_outcome}"
    )

    print()
    print("WAHRSCHEINLICHSTE ERGEBNISSE")
    print("-" * 78)

    for index, score in enumerate(
        prediction.most_likely_scores,
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{score.score:<8} "
            f"{score.probability * 100:6.2f} %"
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
        service = PredictionService(
            connection
        )

        match_id = find_test_match(
            connection
        )

        print("=" * 78)
        print("PREDICTION SERVICE TEST")
        print("=" * 78)

        print(
            f"Wettbewerb:         "
            f"{COMPETITION_ID}"
        )

        print(
            f"Ziel-Spieltag:      "
            f"{TARGET_MATCHDAY}"
        )

        print(
            f"Gefundene Match-ID: "
            f"{match_id}"
        )

        prematch = service.predict_match(
            match_id=match_id,
            mode=PredictionMode.PREMATCH,
        )

        print_prediction(
            "PREMATCH",
            prematch,
        )

        home_lineup, away_lineup = (
            service.get_lineup_coverage(
                match_id
            )
        )

        print()
        print("=" * 78)
        print("LINEUP COVERAGE")
        print("=" * 78)

        print(
            f"Heim-Starter:       "
            f"{home_lineup}"
        )

        print(
            f"Auswärts-Starter:   "
            f"{away_lineup}"
        )

        if service.has_lineup(match_id):
            lineup = service.predict_match(
                match_id=match_id,
                mode=PredictionMode.LINEUP,
            )

            print_prediction(
                "LINEUP",
                lineup,
            )

            print()
            print("=" * 78)
            print("VERGLEICH PREMATCH / LINEUP")
            print("=" * 78)

            print(
                f"Δ Heimtore:         "
                f"{lineup.expected_home_goals - prematch.expected_home_goals:+.4f}"
            )

            print(
                f"Δ Auswärtstore:     "
                f"{lineup.expected_away_goals - prematch.expected_away_goals:+.4f}"
            )

            print(
                f"Δ 1:                "
                f"{(lineup.home_win_probability - prematch.home_win_probability) * 100:+.3f} PP"
            )

            print(
                f"Δ X:                "
                f"{(lineup.draw_probability - prematch.draw_probability) * 100:+.3f} PP"
            )

            print(
                f"Δ 2:                "
                f"{(lineup.away_win_probability - prematch.away_win_probability) * 100:+.3f} PP"
            )

        else:
            print()
            print(
                "LINEUP-Test übersprungen: "
                "Für mindestens eine Mannschaft "
                "fehlt die Startelf."
            )

        print()
        print("=" * 78)
        print("ANTI-LEAK CHECK")
        print("=" * 78)

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE
                competition_id = ?
                AND matchday < ?
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL;
            """,
            (
                COMPETITION_ID,
                TARGET_MATCHDAY,
            ),
        )

        historical_count = int(
            cursor.fetchone()[0]
        )

        cursor.execute(
            """
            SELECT MAX(matchday)
            FROM matches
            WHERE
                competition_id = ?
                AND matchday < ?
                AND home_goals IS NOT NULL
                AND away_goals IS NOT NULL;
            """,
            (
                COMPETITION_ID,
                TARGET_MATCHDAY,
            ),
        )

        highest_matchday = (
            cursor.fetchone()[0]
        )

        print(
            f"Historische Spiele: "
            f"{historical_count}"
        )

        print(
            f"Höchster Spieltag:  "
            f"{highest_matchday}"
        )

        if (
            highest_matchday is not None
            and int(highest_matchday)
            < TARGET_MATCHDAY
        ):
            print(
                "STATUS: OK – Cutoff eingehalten."
            )
        else:
            print(
                "STATUS: FEHLER – Cutoff prüfen!"
            )

        print()
        print("=" * 78)
        print("TEST BEENDET")
        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()