from __future__ import annotations

import math
import sqlite3
from pathlib import Path

from src.services.prediction.historical_data_context import (
    HistoricalDataContext,
)
from src.services.prediction.lineup_strength_service import (
    LineupStrengthService,
)


DATABASE_PATH = Path("data/database/kreisligamanager.db")

COMPETITIONS = (
    (2, "Bundesliga", 5, 34),
    (3, "Regionalliga Südwest", 5, 34),
    (1, "Kreisliga A7", 5, 26),
)

MINIMUM_LINEUP_PLAYERS = 11
MINIMUM_KNOWN_LINEUP_PLAYERS = 8


def percentile(
    values: list[float],
    probability: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
        ordered[lower] * (1.0 - fraction)
        + ordered[upper] * fraction
    )


def standard_deviation(
    values: list[float],
) -> float:
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)

    variance = sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)

    return math.sqrt(variance)


def get_finished_matches(
    connection: sqlite3.Connection,
    competition_id: int,
    matchday: int,
) -> list[tuple[int, int, int]]:
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
            AND home_goals IS NOT NULL
            AND away_goals IS NOT NULL
        ORDER BY match_id;
        """,
        (
            competition_id,
            matchday,
        ),
    )

    return [
        (
            int(row[0]),
            int(row[1]),
            int(row[2]),
        )
        for row in cursor.fetchall()
    ]


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 108)
        print("LINEUP FACTOR DISTRIBUTION – DIAGNOSE")
        print("=" * 108)
        print(
            "Nur vollständige Startelf: "
            f"{MINIMUM_LINEUP_PLAYERS}/11 | "
            "historisch bekannt: mindestens "
            f"{MINIMUM_KNOWN_LINEUP_PLAYERS}/11"
        )
        print()

        all_values: list[float] = []

        for (
            competition_id,
            competition_name,
            start_matchday,
            end_matchday,
        ) in COMPETITIONS:
            values: list[float] = []

            total_team_lineups = 0
            usable_team_lineups = 0

            for matchday in range(
                start_matchday,
                end_matchday + 1,
            ):
                context = HistoricalDataContext(
                    connection=connection,
                    competition_id=competition_id,
                    cutoff_matchday=matchday,
                )

                lineup_service = LineupStrengthService(
                    context
                )

                fixtures = get_finished_matches(
                    connection=connection,
                    competition_id=competition_id,
                    matchday=matchday,
                )

                for (
                    match_id,
                    home_team_id,
                    away_team_id,
                ) in fixtures:
                    for team_id in (
                        home_team_id,
                        away_team_id,
                    ):
                        total_team_lineups += 1

                        lineup = (
                            lineup_service
                            .get_lineup_strength(
                                match_id=match_id,
                                team_id=team_id,
                            )
                        )

                        if (
                            lineup.lineup_players
                            < MINIMUM_LINEUP_PLAYERS
                        ):
                            continue

                        if (
                            lineup.known_players
                            < MINIMUM_KNOWN_LINEUP_PLAYERS
                        ):
                            continue

                        usable_team_lineups += 1
                        values.append(
                            lineup.relative_lineup_factor
                        )

            all_values.extend(values)

            print("=" * 108)
            print(competition_name)
            print("=" * 108)

            coverage = (
                usable_team_lineups
                / total_team_lineups
                * 100.0
                if total_team_lineups
                else 0.0
            )

            print(
                f"Verwendbare Team-Lineups: "
                f"{usable_team_lineups}/"
                f"{total_team_lineups} "
                f"({coverage:.2f}%)"
            )

            if not values:
                print("Keine verwertbaren Werte.")
                print()
                continue

            mean = sum(values) / len(values)
            stddev = standard_deviation(values)

            print(
                f"Minimum:       {min(values):.6f} "
                f"({(min(values) - 1.0) * 100:+.2f}%)"
            )
            print(
                f"P05:           {percentile(values, 0.05):.6f}"
            )
            print(
                f"P10:           {percentile(values, 0.10):.6f}"
            )
            print(
                f"P25:           {percentile(values, 0.25):.6f}"
            )
            print(
                f"Median:        {percentile(values, 0.50):.6f}"
            )
            print(
                f"Mittelwert:    {mean:.6f} "
                f"({(mean - 1.0) * 100:+.3f}%)"
            )
            print(
                f"P75:           {percentile(values, 0.75):.6f}"
            )
            print(
                f"P90:           {percentile(values, 0.90):.6f}"
            )
            print(
                f"P95:           {percentile(values, 0.95):.6f}"
            )
            print(
                f"Maximum:       {max(values):.6f} "
                f"({(max(values) - 1.0) * 100:+.2f}%)"
            )
            print(
                f"StdAbw:        {stddev:.6f} "
                f"({stddev * 100:.3f} PP)"
            )

            below_099 = sum(
                value < 0.99
                for value in values
            )
            below_098 = sum(
                value < 0.98
                for value in values
            )
            above_101 = sum(
                value > 1.01
                for value in values
            )

            print()
            print(
                f"< 0.99:        {below_099:>4} "
                f"({below_099 / len(values) * 100:>6.2f}%)"
            )
            print(
                f"< 0.98:        {below_098:>4} "
                f"({below_098 / len(values) * 100:>6.2f}%)"
            )
            print(
                f"> 1.01:        {above_101:>4} "
                f"({above_101 / len(values) * 100:>6.2f}%)"
            )
            print()

        print("=" * 108)
        print("GESAMT")
        print("=" * 108)

        if all_values:
            mean = sum(all_values) / len(all_values)
            stddev = standard_deviation(all_values)

            print(f"Team-Lineups:   {len(all_values)}")
            print(f"Minimum:        {min(all_values):.6f}")
            print(
                f"P05:            "
                f"{percentile(all_values, 0.05):.6f}"
            )
            print(
                f"P25:            "
                f"{percentile(all_values, 0.25):.6f}"
            )
            print(
                f"Median:         "
                f"{percentile(all_values, 0.50):.6f}"
            )
            print(f"Mittelwert:     {mean:.6f}")
            print(
                f"P75:            "
                f"{percentile(all_values, 0.75):.6f}"
            )
            print(
                f"P95:            "
                f"{percentile(all_values, 0.95):.6f}"
            )
            print(f"Maximum:        {max(all_values):.6f}")
            print(f"StdAbw:         {stddev:.6f}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
