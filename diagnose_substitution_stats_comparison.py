from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")


def main() -> None:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    print("=" * 120)
    print("DIAGNOSE WECHSEL: EVENTS ↔ PLAYER_MATCH_STATS")
    print("=" * 120)
    print(f"Datenbank: {DB_PATH}")
    print()

    event_rows = connection.execute(
        """
        SELECT
            e.match_id,
            e.team_id,
            et.code AS event_type,
            COUNT(*) AS count_events
        FROM events e
        INNER JOIN event_types et
            ON et.event_type_id = e.event_type_id
        WHERE et.code IN (
            'SUBSTITUTION_IN',
            'SUBSTITUTION_OUT'
        )
        GROUP BY
            e.match_id,
            e.team_id,
            et.code
        ORDER BY
            e.match_id,
            e.team_id,
            et.code
        """
    ).fetchall()

    stats_rows = connection.execute(
        """
        SELECT
            match_id,
            team_id,
            SUM(
                CASE
                    WHEN minute_in IS NOT NULL
                         AND minute_in > 0
                    THEN 1
                    ELSE 0
                END
            ) AS stats_in,
            SUM(
                CASE
                    WHEN minute_out IS NOT NULL
                         AND minute_out < 90
                    THEN 1
                    ELSE 0
                END
            ) AS stats_out
        FROM player_match_stats
        GROUP BY
            match_id,
            team_id
        ORDER BY
            match_id,
            team_id
        """
    ).fetchall()

    event_map: dict[
        tuple[int, int],
        dict[str, int],
    ] = defaultdict(
        lambda: {
            "SUBSTITUTION_IN": 0,
            "SUBSTITUTION_OUT": 0,
        }
    )

    for row in event_rows:
        key = (
            int(row["match_id"]),
            int(row["team_id"]),
        )

        event_map[key][
            str(row["event_type"])
        ] = int(
            row["count_events"]
        )

    stats_map: dict[
        tuple[int, int],
        tuple[int, int],
    ] = {}

    for row in stats_rows:
        key = (
            int(row["match_id"]),
            int(row["team_id"]),
        )

        stats_map[key] = (
            int(row["stats_in"] or 0),
            int(row["stats_out"] or 0),
        )

    keys = sorted(
        set(event_map.keys())
        | set(stats_map.keys())
    )

    suspicious = 0

    for match_id, team_id in keys:
        event_in = event_map[
            (match_id, team_id)
        ]["SUBSTITUTION_IN"]

        event_out = event_map[
            (match_id, team_id)
        ]["SUBSTITUTION_OUT"]

        stats_in, stats_out = stats_map.get(
            (match_id, team_id),
            (0, 0),
        )

        if (
            event_in == stats_in
            and event_out == stats_out
        ):
            continue

        suspicious += 1

        team_row = connection.execute(
            """
            SELECT name
            FROM teams
            WHERE team_id = ?
            """,
            (team_id,),
        ).fetchone()

        team_name = (
            team_row["name"]
            if team_row is not None
            else "?"
        )

        print("=" * 120)
        print(
            f"SPIEL {match_id} | "
            f"TEAM {team_id} | "
            f"{team_name}"
        )
        print("-" * 120)
        print(
            f"EVENTS:              "
            f"IN={event_in} OUT={event_out}"
        )
        print(
            f"PLAYER_MATCH_STATS:  "
            f"IN={stats_in} OUT={stats_out}"
        )

        if event_in != stats_in:
            print(
                f"Δ IN:  {stats_in - event_in:+d}"
            )

        if event_out != stats_out:
            print(
                f"Δ OUT: {stats_out - event_out:+d}"
            )

        print()

        detail_rows = connection.execute(
            """
            SELECT
                pms.player_id,
                p.first_name,
                p.last_name,
                pms.is_starting,
                pms.minute_in,
                pms.minute_out,
                pms.minutes_played
            FROM player_match_stats pms
            LEFT JOIN players p
                ON p.player_id = pms.player_id
            WHERE
                pms.match_id = ?
                AND pms.team_id = ?
            ORDER BY
                pms.is_starting DESC,
                pms.minute_in,
                pms.minute_out,
                pms.player_id
            """,
            (
                match_id,
                team_id,
            ),
        ).fetchall()

        for row in detail_rows:
            name = " ".join(
                part
                for part in (
                    row["first_name"] or "",
                    row["last_name"] or "",
                )
                if part
            ) or "-"

            print(
                f"  player_id={row['player_id']:<4} | "
                f"start={row['is_starting']} | "
                f"in={row['minute_in']} | "
                f"out={row['minute_out']} | "
                f"min={row['minutes_played']} | "
                f"{name}"
            )

        print()

    print("=" * 120)
    print("ZUSAMMENFASSUNG")
    print("=" * 120)
    print(
        f"Verglichene Spiel/Team-Kombinationen: "
        f"{len(keys)}"
    )
    print(
        f"Auffällige Kombinationen:             "
        f"{suspicious}"
    )

    if suspicious == 0:
        print()
        print(
            "ERGEBNIS: Events und player_match_stats "
            "stimmen bei allen Wechselzählungen überein."
        )
    else:
        print()
        print(
            "ERGEBNIS: Differenzen gefunden. "
            "Die Blöcke oben zeigen, ob StatsBuilder "
            "oder Validator falsch zählt."
        )

    print("=" * 120)

    connection.close()


if __name__ == "__main__":
    main()
