from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.historical_data_context import HistoricalDataContext
from src.services.prediction.poisson_model import PoissonModel
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
TARGET_MATCHDAY = 10


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                matches.match_id,
                home_teams.name AS home_name,
                away_teams.name AS away_name,
                matches.home_team_id,
                matches.away_team_id,
                matches.home_goals,
                matches.away_goals
            FROM matches
            INNER JOIN teams AS home_teams
                ON home_teams.team_id = matches.home_team_id
            INNER JOIN teams AS away_teams
                ON away_teams.team_id = matches.away_team_id
            WHERE
                matches.competition_id = ?
                AND matches.matchday = ?
            ORDER BY matches.match_id;
            """,
            (COMPETITION_ID, TARGET_MATCHDAY),
        )
        fixtures = cursor.fetchall()

        if not fixtures:
            raise RuntimeError(
                f"Keine Spiele für Spieltag {TARGET_MATCHDAY} gefunden."
            )

        context = HistoricalDataContext(
            connection=connection,
            competition_id=COMPETITION_ID,
            cutoff_matchday=TARGET_MATCHDAY,
        )
        strength_service = TeamStrengthService(context)
        poisson = PoissonModel(max_goals=10)
        league = strength_service.get_league_strength()

        historical = context.get_matches()
        leaked = [
            match
            for match in historical
            if match.matchday >= TARGET_MATCHDAY
        ]

        print("=" * 84)
        print("BUNDESLIGA 2025/26 – ERSTE ECHTE PREDICTION")
        print("=" * 84)
        print(f"Wettbewerb-ID:                  {COMPETITION_ID}")
        print(f"Prognostizierter Spieltag:      {TARGET_MATCHDAY}")
        print(f"Historische Spiele verwendet:   {len(historical)}")
        print(
            "Höchster bekannter Spieltag:    "
            f"{max(m.matchday for m in historical)}"
        )
        print(f"Zukünftige Spiele im Modell:    {len(leaked)}")
        print()
        print(
            "WICHTIG: Die echten Ergebnisse von Spieltag 10 werden "
            "erst nach der Prediction ausgegeben."
        )

        predictions = []

        for fixture in fixtures:
            home = strength_service.get_team_strength(
                int(fixture["home_team_id"])
            )
            away = strength_service.get_team_strength(
                int(fixture["away_team_id"])
            )

            result = poisson.predict(
                home_team=home,
                away_team=away,
                league=league,
            )

            predictions.append((fixture, result))

        print()
        print("=" * 84)
        print("PREDICTIONS – NUR DATEN AUS SPIELTAG 1–9")
        print("=" * 84)

        for fixture, prediction in predictions:
            print()
            print(
                f"{fixture['home_name']} - {fixture['away_name']}"
            )
            print(
                f"  Erwartete Tore: "
                f"{prediction.expected_goals.home:.2f} : "
                f"{prediction.expected_goals.away:.2f}"
            )
            print(
                f"  1: {prediction.home_win_probability * 100:5.1f}% | "
                f"X: {prediction.draw_probability * 100:5.1f}% | "
                f"2: {prediction.away_win_probability * 100:5.1f}%"
            )

            top_scores = " | ".join(
                f"{score.score} "
                f"{score.probability * 100:.1f}%"
                for score in prediction.most_likely_scores
            )
            print(f"  Top-Ergebnisse: {top_scores}")

        print()
        print("=" * 84)
        print("JETZT ERST: TATSÄCHLICHE ERGEBNISSE")
        print("=" * 84)

        correct = 0

        for fixture, prediction in predictions:
            home_goals = fixture["home_goals"]
            away_goals = fixture["away_goals"]

            if home_goals is None or away_goals is None:
                actual = "offen"
                actual_outcome = None
            else:
                home_goals = int(home_goals)
                away_goals = int(away_goals)
                actual = f"{home_goals}:{away_goals}"

                if home_goals > away_goals:
                    actual_outcome = "1"
                elif home_goals < away_goals:
                    actual_outcome = "2"
                else:
                    actual_outcome = "X"

            probabilities = {
                "1": prediction.home_win_probability,
                "X": prediction.draw_probability,
                "2": prediction.away_win_probability,
            }
            predicted_outcome = max(
                probabilities,
                key=probabilities.get,
            )

            hit = (
                actual_outcome is not None
                and predicted_outcome == actual_outcome
            )
            if hit:
                correct += 1

            marker = "✔" if hit else "✖"

            print(
                f"{marker} {fixture['home_name']} - "
                f"{fixture['away_name']}: "
                f"Prediction {predicted_outcome} | "
                f"Real {actual}"
            )

        completed = sum(
            1
            for fixture, _ in predictions
            if (
                fixture["home_goals"] is not None
                and fixture["away_goals"] is not None
            )
        )

        print()
        print("=" * 84)
        print("ERSTER CHECK")
        print("=" * 84)
        print(f"Abgeschlossene Spiele: {completed}")
        print(f"1X2-Treffer:           {correct}/{completed}")

        if completed:
            print(
                f"Trefferquote:          "
                f"{correct / completed * 100:.1f}%"
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
