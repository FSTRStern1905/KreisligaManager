from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

MATCH_ID = 789

GOAL_CODES = {
    "GOAL",
    "OWN_GOAL",
    "PENALTY_GOAL",
}


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        match_row = connection.execute(
            """
            SELECT
                matches.match_id,
                matches.home_team_id,
                matches.away_team_id,
                matches.home_goals,
                matches.away_goals,
                home.name AS home_team,
                away.name AS away_team
            FROM matches
            LEFT JOIN teams AS home
                ON home.team_id =
                   matches.home_team_id
            LEFT JOIN teams AS away
                ON away.team_id =
                   matches.away_team_id
            WHERE matches.match_id = ?
            """,
            (MATCH_ID,),
        ).fetchone()

        if match_row is None:
            raise RuntimeError(
                "Spiel 789 wurde nicht gefunden."
            )

        print("=" * 110)
        print("DIAGNOSE TOR-EVENTS SPIEL 789")
        print("=" * 110)
        print(
            f"{match_row['home_team']} - "
            f"{match_row['away_team']}"
        )
        print(
            f"Ergebnis in matches: "
            f"{match_row['home_goals']}:"
            f"{match_row['away_goals']}"
        )
        print(
            f"Interne Team-IDs: "
            f"{match_row['home_team_id']} / "
            f"{match_row['away_team_id']}"
        )
        print()

        event_rows = connection.execute(
            """
            SELECT
                events.event_id,
                event_types.code AS event_type_code,
                events.minute,
                events.second,
                events.team_id,
                teams.name AS team_name,
                events.player_id,
                players.first_name,
                players.last_name,
                events.related_player_id,
                events.value,
                events.notes
            FROM events
            INNER JOIN event_types
                ON event_types.event_type_id =
                   events.event_type_id
            LEFT JOIN teams
                ON teams.team_id =
                   events.team_id
            LEFT JOIN players
                ON players.player_id =
                   events.player_id
            WHERE
                events.match_id = ?
                AND event_types.code IN (
                    'GOAL',
                    'OWN_GOAL',
                    'PENALTY_GOAL'
                )
            ORDER BY
                events.minute,
                events.second,
                events.event_id
            """,
            (MATCH_ID,),
        ).fetchall()

        print("TOR-EVENTS IN DB")
        print("-" * 110)

        for index, row in enumerate(
            event_rows,
            start=1,
        ):
            player_name = " ".join(
                part
                for part in (
                    row["first_name"] or "",
                    row["last_name"] or "",
                )
                if part
            ) or "-"

            print(
                f"{index:>2}. "
                f"event_id={row['event_id']} | "
                f"{row['minute']}' | "
                f"{row['event_type_code']} | "
                f"team_id={row['team_id']} "
                f"({row['team_name'] or '-'}) | "
                f"player_id={row['player_id']} "
                f"({player_name})"
            )

            print(
                f"    value: {row['value']!r}"
            )
            print(
                f"    notes: {row['notes']!r}"
            )
            print()

        print(
            f"Tor-Events gesamt: {len(event_rows)}"
        )
        print()

        stats_rows = connection.execute(
            """
            SELECT
                player_match_stats.player_match_stat_id,
                player_match_stats.team_id,
                teams.name AS team_name,
                player_match_stats.player_id,
                players.first_name,
                players.last_name,
                player_match_stats.goals,
                player_match_stats.own_goals,
                player_match_stats.assists,
                player_match_stats.yellow_cards,
                player_match_stats.red_cards,
                player_match_stats.minutes_played
            FROM player_match_stats
            LEFT JOIN teams
                ON teams.team_id =
                   player_match_stats.team_id
            LEFT JOIN players
                ON players.player_id =
                   player_match_stats.player_id
            WHERE player_match_stats.match_id = ?
            ORDER BY
                player_match_stats.team_id,
                players.last_name,
                players.first_name
            """,
            (MATCH_ID,),
        ).fetchall()

        print("=" * 110)
        print("PLAYER_MATCH_STATS")
        print("-" * 110)

        total_stat_goals = 0

        for row in stats_rows:
            player_name = " ".join(
                part
                for part in (
                    row["first_name"] or "",
                    row["last_name"] or "",
                )
                if part
            ) or "-"

            goals = int(
                row["goals"] or 0
            )
            own_goals = int(
                row["own_goals"] or 0
            )

            total_stat_goals += (
                goals + own_goals
            )

            if (
                goals
                or own_goals
                or row["yellow_cards"]
                or row["red_cards"]
            ):
                print(
                    f"stat_id={row['player_match_stat_id']} | "
                    f"team_id={row['team_id']} "
                    f"({row['team_name'] or '-'}) | "
                    f"player_id={row['player_id']} "
                    f"({player_name}) | "
                    f"goals={goals} | "
                    f"own_goals={own_goals} | "
                    f"yellow={row['yellow_cards']} | "
                    f"red={row['red_cards']} | "
                    f"minutes={row['minutes_played']}"
                )

        print()
        print(
            f"player_match_stats Zeilen: "
            f"{len(stats_rows)}"
        )
        print(
            f"Tore in player_match_stats: "
            f"{total_stat_goals}"
        )

        print()
        print("=" * 110)

        expected_goals = int(
            (match_row["home_goals"] or 0)
            + (match_row["away_goals"] or 0)
        )

        print(
            f"Ergebnis-Tore:            {expected_goals}"
        )
        print(
            f"Event-Tore:               {len(event_rows)}"
        )
        print(
            f"player_match_stats-Tore:  {total_stat_goals}"
        )

        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
