from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.lineup_strength_service import (
    LineupStrengthService,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_ID = 2
START_MATCHDAY = 5
TOP_N = 20


@dataclass(frozen=True, slots=True)
class LineupCase:
    matchday: int
    match_id: int
    team_name: str
    opponent_name: str
    side: str
    lineup_players: int
    known_players: int
    lineup_factor: float
    expected_factor: float
    relative_factor: float


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        last_matchday = _get_last_matchday(
            connection,
            COMPETITION_ID,
        )

        cases: list[LineupCase] = []
        total_teams = 0
        complete_lineups = 0
        fully_known_lineups = 0

        print("=" * 120)
        print("LINEUP EXTREMES TEST")
        print("=" * 120)
        print(f"Wettbewerb-ID:   {COMPETITION_ID}")
        print(
            f"Spieltage:        "
            f"{START_MATCHDAY}–{last_matchday}"
        )
        print()

        for matchday in range(
            START_MATCHDAY,
            last_matchday + 1,
        ):
            context = HistoricalDataContext(
                connection=connection,
                competition_id=COMPETITION_ID,
                cutoff_matchday=matchday,
            )
            service = LineupStrengthService(context)

            fixtures = _get_fixtures(
                connection=connection,
                competition_id=COMPETITION_ID,
                matchday=matchday,
            )

            for fixture in fixtures:
                for (
                    side,
                    team_id,
                    team_name,
                    opponent_name,
                ) in (
                    (
                        "H",
                        fixture["home_team_id"],
                        fixture["home_team_name"],
                        fixture["away_team_name"],
                    ),
                    (
                        "A",
                        fixture["away_team_id"],
                        fixture["away_team_name"],
                        fixture["home_team_name"],
                    ),
                ):
                    result = service.get_lineup_strength(
                        match_id=fixture["match_id"],
                        team_id=team_id,
                    )

                    total_teams += 1

                    if result.lineup_players >= 11:
                        complete_lineups += 1

                    if (
                        result.lineup_players >= 11
                        and result.known_players
                        >= result.lineup_players
                    ):
                        fully_known_lineups += 1

                    # Only compare complete and fully historically
                    # evaluable starting XIs.
                    if (
                        result.lineup_players < 11
                        or result.known_players
                        < result.lineup_players
                    ):
                        continue

                    cases.append(
                        LineupCase(
                            matchday=matchday,
                            match_id=fixture["match_id"],
                            team_name=team_name,
                            opponent_name=opponent_name,
                            side=side,
                            lineup_players=(
                                result.lineup_players
                            ),
                            known_players=(
                                result.known_players
                            ),
                            lineup_factor=(
                                result.lineup_factor
                            ),
                            expected_factor=(
                                result.expected_lineup_factor
                            ),
                            relative_factor=(
                                result.relative_lineup_factor
                            ),
                        )
                    )

            print(
                f"ST {matchday:>2}: "
                f"{len(fixtures):>2} Spiele verarbeitet"
            )

        print()
        print("=" * 120)
        print("COVERAGE")
        print("=" * 120)
        print(f"Team-Aufstellungen geprüft: {total_teams}")
        print(
            f"Komplette Startelf:         "
            f"{complete_lineups}/{total_teams} "
            f"({_pct(complete_lineups, total_teams):.2f}%)"
        )
        print(
            f"Voll historisch bekannt:    "
            f"{fully_known_lineups}/{total_teams} "
            f"({_pct(fully_known_lineups, total_teams):.2f}%)"
        )
        print(
            f"Für Extremtest verwendet:   {len(cases)}"
        )

        if not cases:
            print("Keine vollständig auswertbaren Lineups.")
            return

        weakest = sorted(
            cases,
            key=lambda item: item.relative_factor,
        )[:TOP_N]

        strongest = sorted(
            cases,
            key=lambda item: item.relative_factor,
            reverse=True,
        )[:TOP_N]

        _print_cases(
            "20 SCHWÄCHSTE STARTELF-ABWEICHUNGEN",
            weakest,
        )
        _print_cases(
            "20 STÄRKSTE STARTELF-ABWEICHUNGEN",
            strongest,
        )

        factors = [
            case.relative_factor
            for case in cases
        ]

        below_99 = sum(
            factor < 0.99
            for factor in factors
        )
        below_98 = sum(
            factor < 0.98
            for factor in factors
        )
        below_97 = sum(
            factor < 0.97
            for factor in factors
        )
        above_101 = sum(
            factor > 1.01
            for factor in factors
        )
        above_102 = sum(
            factor > 1.02
            for factor in factors
        )
        above_103 = sum(
            factor > 1.03
            for factor in factors
        )

        print()
        print("=" * 120)
        print("VERTEILUNG")
        print("=" * 120)
        print(
            f"Minimum:              {min(factors):.4f} "
            f"({(min(factors) - 1.0) * 100:+.2f}%)"
        )
        print(
            f"Maximum:              {max(factors):.4f} "
            f"({(max(factors) - 1.0) * 100:+.2f}%)"
        )
        print(
            f"Durchschnitt:         "
            f"{sum(factors) / len(factors):.4f}"
        )
        print()
        print(f"< 0.99:               {below_99}")
        print(f"< 0.98:               {below_98}")
        print(f"< 0.97:               {below_97}")
        print(f"> 1.01:               {above_101}")
        print(f"> 1.02:               {above_102}")
        print(f"> 1.03:               {above_103}")

    finally:
        connection.close()


def _print_cases(
    title: str,
    cases: list[LineupCase],
) -> None:
    print()
    print("=" * 120)
    print(title)
    print("=" * 120)
    print(
        f"{'#':>2} {'ST':>2} {'S':>1} "
        f"{'Mannschaft':<31} "
        f"{'Gegner':<31} "
        f"{'Lineup':>7} {'Erwart.':>7} "
        f"{'Relativ':>7} {'Abw.%':>7}"
    )

    for index, case in enumerate(cases, start=1):
        deviation = (
            case.relative_factor - 1.0
        ) * 100.0

        print(
            f"{index:>2} "
            f"{case.matchday:>2} "
            f"{case.side:>1} "
            f"{case.team_name[:31]:<31} "
            f"{case.opponent_name[:31]:<31} "
            f"{case.lineup_factor:>7.3f} "
            f"{case.expected_factor:>7.3f} "
            f"{case.relative_factor:>7.3f} "
            f"{deviation:>+6.2f}%"
        )


def _get_fixtures(
    connection: sqlite3.Connection,
    competition_id: int,
    matchday: int,
) -> list[dict]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            matches.match_id,
            matches.home_team_id,
            matches.away_team_id,
            home_team.name AS home_team_name,
            away_team.name AS away_team_name
        FROM matches
        INNER JOIN teams AS home_team
            ON home_team.team_id = matches.home_team_id
        INNER JOIN teams AS away_team
            ON away_team.team_id = matches.away_team_id
        WHERE
            matches.competition_id = ?
            AND matches.matchday = ?
        ORDER BY matches.match_id;
        """,
        (
            competition_id,
            matchday,
        ),
    )

    return [
        dict(row)
        for row in cursor.fetchall()
    ]


def _get_last_matchday(
    connection: sqlite3.Connection,
    competition_id: int,
) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT MAX(matchday)
        FROM matches
        WHERE
            competition_id = ?
            AND matchday IS NOT NULL;
        """,
        (competition_id,),
    )

    row = cursor.fetchone()

    if row is None or row[0] is None:
        raise ValueError(
            "Keine Spieltage gefunden."
        )

    return int(row[0])


def _pct(
    value: int,
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    return value / total * 100.0


if __name__ == "__main__":
    main()
