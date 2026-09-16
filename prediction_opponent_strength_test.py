from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.opponent_strength_service import (
    OpponentStrength,
    OpponentStrengthService,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")

MIN_FINISHED_MATCHES = 80
MIN_MATCHDAYS = 10
TOP_TEAMS = 5


@dataclass(frozen=True, slots=True)
class Competition:
    competition_id: int
    name: str
    season_name: str
    finished_matches: int
    last_matchday: int


@dataclass(frozen=True, slots=True)
class TeamResult:
    team_id: int
    team_name: str
    strength: OpponentStrength


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        competitions = _find_competitions(connection)

        print("=" * 110)
        print("PREDICTION ENGINE – OPPONENT STRENGTH PLAUSIBILITY TEST")
        print("=" * 110)
        print(f"Echte Wettbewerbe gefunden: {len(competitions)}")
        print()

        for competition in competitions:
            _test_competition(
                connection=connection,
                competition=competition,
            )

    finally:
        connection.close()


def _test_competition(
    connection: sqlite3.Connection,
    competition: Competition,
) -> None:
    cutoff_matchday = competition.last_matchday + 1

    context = HistoricalDataContext(
        connection=connection,
        competition_id=competition.competition_id,
        cutoff_matchday=cutoff_matchday,
    )

    service = OpponentStrengthService(context)

    teams = _get_teams(
        connection=connection,
        competition_id=competition.competition_id,
    )

    results: list[TeamResult] = []

    for team_id, team_name in teams:
        strength = service.get_team_opponent_strength(
            team_id
        )

        if strength.matches_used <= 0:
            continue

        results.append(
            TeamResult(
                team_id=team_id,
                team_name=team_name,
                strength=strength,
            )
        )

    if not results:
        return

    results.sort(
        key=lambda item: item.strength.schedule_factor,
        reverse=True,
    )

    average_factor = (
        sum(
            item.strength.schedule_factor
            for item in results
        )
        / len(results)
    )

    minimum = min(
        item.strength.schedule_factor
        for item in results
    )
    maximum = max(
        item.strength.schedule_factor
        for item in results
    )

    print("=" * 110)
    print(
        f"{competition.name} | {competition.season_name} "
        f"| ID {competition.competition_id}"
    )
    print("-" * 110)
    print(
        f"Spiele: {competition.finished_matches} | "
        f"letzter ST: {competition.last_matchday} | "
        f"Teams: {len(results)} | "
        f"Ø Schedule-Faktor: {average_factor:.4f} | "
        f"Range: {minimum:.4f}–{maximum:.4f}"
    )
    print()

    print("SCHWERSTER BISHERIGER SPIELPLAN")
    for item in results[:TOP_TEAMS]:
        _print_team(item)

    print()
    print("LEICHTESTER BISHERIGER SPIELPLAN")
    for item in reversed(results[-TOP_TEAMS:]):
        _print_team(item)

    print()


def _print_team(
    item: TeamResult,
) -> None:
    strength = item.strength

    print(
        f"  {item.team_name:<42} "
        f"Faktor {strength.schedule_factor:>7.4f} | "
        f"Gegner-Angriff {strength.average_opponent_attack:>7.4f} | "
        f"Gegner-Def. {strength.average_opponent_defense:>7.4f} | "
        f"Spiele {strength.matches_used:>2}"
    )


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


def _get_teams(
    connection: sqlite3.Connection,
    competition_id: int,
) -> list[tuple[int, str]]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT
            teams.team_id,
            teams.name
        FROM teams
        INNER JOIN (
            SELECT
                home_team_id AS team_id
            FROM matches
            WHERE competition_id = ?

            UNION

            SELECT
                away_team_id AS team_id
            FROM matches
            WHERE competition_id = ?
        ) AS competition_teams
            ON competition_teams.team_id = teams.team_id
        ORDER BY
            teams.name
        """,
        (
            competition_id,
            competition_id,
        ),
    )

    return [
        (
            int(row["team_id"]),
            str(row["name"]),
        )
        for row in cursor.fetchall()
    ]


if __name__ == "__main__":
    main()
