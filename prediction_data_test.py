from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.prediction.historical_data_context import HistoricalDataContext
from src.services.prediction.team_strength_service import TeamStrengthService


DATABASE_PATH = Path("data/database/kreisligamanager.db")
TARGET_COMPETITION = "Bundesliga"
TARGET_SEASON = "2025/26"
CUTOFF_MATCHDAY = 10


def find_competitions(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            competitions.competition_id,
            competitions.name AS competition_name,
            seasons.name AS season_name,
            COUNT(DISTINCT matches.match_id) AS match_count,
            MIN(matches.matchday) AS first_matchday,
            MAX(matches.matchday) AS last_matchday
        FROM competitions
        LEFT JOIN seasons
            ON seasons.season_id = competitions.season_id
        LEFT JOIN matches
            ON matches.competition_id = competitions.competition_id
        WHERE
            LOWER(competitions.name) LIKE ?
            AND LOWER(seasons.name) LIKE ?
        GROUP BY
            competitions.competition_id,
            competitions.name,
            seasons.name
        ORDER BY
            match_count DESC,
            competitions.competition_id;
        """,
        (
            f"%{TARGET_COMPETITION.lower()}%",
            f"%{TARGET_SEASON.lower()}%",
        ),
    )

    return cursor.fetchall()


def load_team_names(
    connection: sqlite3.Connection,
    competition_id: int,
) -> dict[int, str]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT DISTINCT
            teams.team_id,
            teams.name
        FROM teams
        INNER JOIN matches
            ON (
                matches.home_team_id = teams.team_id
                OR matches.away_team_id = teams.team_id
            )
        WHERE matches.competition_id = ?
        ORDER BY teams.name;
        """,
        (competition_id,),
    )

    return {
        int(row[0]): str(row[1])
        for row in cursor.fetchall()
    }


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        competitions = find_competitions(connection)

        print("=" * 72)
        print("PREDICTION-DATENTEST")
        print("=" * 72)

        if not competitions:
            print("Keine passende Bundesliga 2025/26 gefunden.")
            print(f"Wettbewerb-Suche: {TARGET_COMPETITION}")
            print(f"Saison-Suche:      {TARGET_SEASON}")
            return

        print("Gefundene Wettbewerbe:")
        for row in competitions:
            print(
                f"  ID {row['competition_id']} | "
                f"{row['competition_name']} | "
                f"{row['season_name']} | "
                f"{row['match_count']} Spiele | "
                f"ST {row['first_matchday']}–{row['last_matchday']}"
            )

        selected = competitions[0]
        competition_id = int(selected["competition_id"])

        context = HistoricalDataContext(
            connection=connection,
            competition_id=competition_id,
            cutoff_matchday=CUTOFF_MATCHDAY,
        )
        historical_matches = context.get_matches()

        print()
        print("=" * 72)
        print(f"ANTI-SCHUMMEL-TEST – STICHTAG {CUTOFF_MATCHDAY}")
        print("=" * 72)

        highest_matchday = (
            max(match.matchday for match in historical_matches)
            if historical_matches
            else None
        )
        leaked_matches = [
            match
            for match in historical_matches
            if match.matchday >= CUTOFF_MATCHDAY
        ]

        print(f"Historische Spiele:             {len(historical_matches)}")
        print(f"Höchster verwendeter Spieltag:  {highest_matchday}")
        print(
            f"Spiele aus ST {CUTOFF_MATCHDAY}+:              "
            f"{len(leaked_matches)}"
        )

        if leaked_matches:
            raise RuntimeError("FEHLER: zukünftige Ergebnisse sichtbar.")

        print("STATUS: OK – keine zukünftigen Ergebnisse sichtbar.")

        service = TeamStrengthService(context)
        league = service.get_league_strength()

        print()
        print("=" * 72)
        print("LIGAWERTE BIS ZUM STICHTAG")
        print("=" * 72)
        print(f"Spiele:             {league.matches_played}")
        print(f"Ø Heimtore:         {league.average_home_goals:.3f}")
        print(f"Ø Auswärtstore:     {league.average_away_goals:.3f}")
        print(f"Ø Tore gesamt:      {league.average_total_goals:.3f}")

        team_names = load_team_names(connection, competition_id)

        print()
        print("=" * 72)
        print("MANNSCHAFTSSTÄRKEN BIS ZUM STICHTAG")
        print("=" * 72)

        for team_id, team_name in team_names.items():
            strength = service.get_team_strength(team_id)

            print()
            print(team_name)
            print(f"  Spiele:             {strength.matches_played}")
            print(
                f"  Tore:                "
                f"{strength.goals_for}:{strength.goals_against}"
            )
            print(f"  Angriff:             {strength.attack_strength:.3f}")
            print(f"  Defensive:           {strength.defense_strength:.3f}")
            print(
                f"  Heim-Angriff:        "
                f"{strength.home_attack_strength:.3f}"
            )
            print(
                f"  Heim-Defensive:      "
                f"{strength.home_defense_strength:.3f}"
            )
            print(
                f"  Auswärts-Angriff:    "
                f"{strength.away_attack_strength:.3f}"
            )
            print(
                f"  Auswärts-Defensive:  "
                f"{strength.away_defense_strength:.3f}"
            )

        print()
        print("=" * 72)
        print("TEST ABGESCHLOSSEN")
        print("=" * 72)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
