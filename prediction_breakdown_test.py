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

TARGET_MATCHDAY = 7
HOME_SEARCH = "Leiwen"
AWAY_SEARCH = "Ehrang"


def find_match(
    connection: sqlite3.Connection,
) -> int:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            m.match_id,
            m.competition_id,
            m.matchday,
            ht.name,
            at.name
        FROM matches m
        INNER JOIN teams ht
            ON ht.team_id = m.home_team_id
        INNER JOIN teams at
            ON at.team_id = m.away_team_id
        WHERE
            m.matchday = ?
            AND ht.name LIKE ?
            AND at.name LIKE ?
        ORDER BY
            m.competition_id,
            m.match_id;
        """,
        (
            TARGET_MATCHDAY,
            f"%{HOME_SEARCH}%",
            f"%{AWAY_SEARCH}%",
        ),
    )

    rows = cursor.fetchall()

    if not rows:
        raise RuntimeError(
            "Kein passendes Spiel gefunden."
        )

    print()
    print("Gefundene Kandidaten:")
    print("-" * 78)

    for row in rows:
        print(
            f"Match-ID {row[0]:<6} | "
            f"Competition {row[1]:<4} | "
            f"ST {row[2]:<2} | "
            f"{row[3]} - {row[4]}"
        )

    print()

    exact_candidates = [
        row
        for row in rows
        if (
            "II" in str(row[3])
            and "III" not in str(row[3])
            and "III" not in str(row[4])
        )
    ]

    if len(exact_candidates) == 1:
        selected = exact_candidates[0]

    elif len(rows) == 1:
        selected = rows[0]

    else:
        print(
            "Mehrere Kandidaten vorhanden."
        )
        print(
            "Bitte gewünschte Match-ID oben auswählen."
        )
        raise RuntimeError(
            "Spiel konnte nicht eindeutig "
            "bestimmt werden."
        )

    print(
        f"Ausgewählt: Match-ID {selected[0]} | "
        f"Competition {selected[1]} | "
        f"ST {selected[2]} | "
        f"{selected[3]} - {selected[4]}"
    )

    return int(
        selected[0]
    )


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        service = PredictionService(
            connection
        )

        match_id = find_match(
            connection
        )

        breakdown = (
            service.get_prediction_breakdown(
                match_id=match_id,
                mode=PredictionMode.PREMATCH,
            )
        )

        details = breakdown.details

        print()
        print("=" * 78)
        print("PROGNOSE-BREAKDOWN")
        print("=" * 78)

        print(
            f"Match-ID:           "
            f"{breakdown.match_id}"
        )

        print(
            f"Competition-ID:     "
            f"{breakdown.competition_id}"
        )

        print(
            f"Spiel:              "
            f"{breakdown.home_team_name} - "
            f"{breakdown.away_team_name}"
        )

        print(
            f"Cutoff:             "
            f"Spieltag {breakdown.cutoff_matchday}"
        )

        print(
            f"Historische Spiele: "
            f"{breakdown.historical_matches}"
        )

        print()
        print("LIGA-BASIS")
        print("-" * 78)

        print(
            f"Ø Heimtore:         "
            f"{details.league_average_home_goals:.4f}"
        )

        print(
            f"Ø Auswärtstore:     "
            f"{details.league_average_away_goals:.4f}"
        )

        print()
        print("TEAMSTÄRKEN")
        print("-" * 78)

        print(
            f"Heim Angriff:       "
            f"{details.home_attack_strength:.4f}"
        )

        print(
            f"Heim Defensive:     "
            f"{details.home_defense_strength:.4f}"
        )

        print(
            f"Auswärts Angriff:   "
            f"{details.away_attack_strength:.4f}"
        )

        print(
            f"Auswärts Defensive: "
            f"{details.away_defense_strength:.4f}"
        )

        print()
        print("ANGEWENDETE FAKTOREN")
        print("-" * 78)

        print(
            f"Form Heim:          "
            f"{details.home_form_factor:.4f}"
        )

        print(
            f"Form Auswärts:      "
            f"{details.away_form_factor:.4f}"
        )

        print(
            f"Gegner Heim:        "
            f"{details.home_opponent_factor:.4f}"
        )

        print(
            f"Gegner Auswärts:    "
            f"{details.away_opponent_factor:.4f}"
        )

        print(
            f"Spieler Heim:       "
            f"{details.home_player_factor:.4f}"
        )

        print(
            f"Spieler Auswärts:   "
            f"{details.away_player_factor:.4f}"
        )

        print(
            f"Lineup Heim:        "
            f"{details.home_lineup_factor:.4f}"
        )

        print(
            f"Lineup Auswärts:    "
            f"{details.away_lineup_factor:.4f}"
        )

        print()
        print("RECHENKETTE")
        print("-" * 78)

        print(
            f"{'Stufe':<22}"
            f"{'Heim':>12}"
            f"{'Auswärts':>12}"
        )

        print("-" * 78)

        for step in details.steps:
            print(
                f"{step.name:<22}"
                f"{step.home:>12.4f}"
                f"{step.away:>12.4f}"
            )

        print()
        print("FINAL")
        print("-" * 78)

        print(
            f"Erwartete Tore:     "
            f"{details.final_expected_goals.home:.4f}"
            f" : "
            f"{details.final_expected_goals.away:.4f}"
        )

        print()
        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()