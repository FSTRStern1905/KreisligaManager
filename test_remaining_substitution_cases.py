from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")
MATCH_IDS = (251, 260)


def name(row: sqlite3.Row) -> str:
    return " ".join(
        part
        for part in (
            row["first_name"] or "",
            row["last_name"] or "",
        )
        if part
    ).strip()


def main() -> None:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        for match_id in MATCH_IDS:
            match = connection.execute(
                """
                SELECT
                    m.match_id,
                    m.matchday,
                    m.external_id,
                    ht.name AS home_team,
                    at.name AS away_team
                FROM matches m
                JOIN teams ht
                    ON ht.team_id = m.home_team_id
                JOIN teams at
                    ON at.team_id = m.away_team_id
                WHERE m.match_id = ?
                """,
                (match_id,),
            ).fetchone()

            if match is None:
                continue

            print()
            print("=" * 100)
            print(
                f"SPIEL {match_id} | ST {match['matchday']} | "
                f"{match['home_team']} - {match['away_team']}"
            )
            print(f"External-ID: {match['external_id']}")
            print("=" * 100)

            lineups = connection.execute(
                """
                SELECT
                    l.team_id,
                    l.player_id,
                    l.is_starting,
                    p.first_name,
                    p.last_name,
                    t.name AS team_name
                FROM lineups l
                JOIN players p
                    ON p.player_id = l.player_id
                LEFT JOIN teams t
                    ON t.team_id = l.team_id
                WHERE l.match_id = ?
                ORDER BY
                    l.team_id,
                    l.is_starting DESC,
                    l.lineup_id
                """,
                (match_id,),
            ).fetchall()

            print()
            print("LINEUPS")
            print("-" * 100)
            print(f"Zeilen: {len(lineups)}")

            lineup_summary = connection.execute(
                """
                SELECT
                    l.team_id,
                    t.name AS team_name,
                    COUNT(*) AS total,
                    SUM(
                        CASE WHEN l.is_starting = 1
                        THEN 1 ELSE 0 END
                    ) AS starters
                FROM lineups l
                LEFT JOIN teams t
                    ON t.team_id = l.team_id
                WHERE l.match_id = ?
                GROUP BY l.team_id, t.name
                ORDER BY l.team_id
                """,
                (match_id,),
            ).fetchall()

            for row in lineup_summary:
                print(
                    f"team_id={row['team_id']} | "
                    f"{row['team_name']} | "
                    f"Kader={row['total']} | "
                    f"Starter={row['starters']}"
                )

            stats_summary = connection.execute(
                """
                SELECT
                    pms.team_id,
                    t.name AS team_name,
                    COUNT(*) AS total,
                    SUM(
                        CASE WHEN pms.is_starting = 1
                        THEN 1 ELSE 0 END
                    ) AS starters,
                    SUM(
                        CASE WHEN pms.was_substituted_in = 1
                        THEN 1 ELSE 0 END
                    ) AS sub_in,
                    SUM(
                        CASE WHEN pms.was_substituted_out = 1
                        THEN 1 ELSE 0 END
                    ) AS sub_out
                FROM player_match_stats pms
                LEFT JOIN teams t
                    ON t.team_id = pms.team_id
                WHERE pms.match_id = ?
                GROUP BY pms.team_id, t.name
                ORDER BY pms.team_id
                """,
                (match_id,),
            ).fetchall()

            print()
            print("PLAYER_MATCH_STATS")
            print("-" * 100)

            for row in stats_summary:
                print(
                    f"team_id={row['team_id']} | "
                    f"{row['team_name']} | "
                    f"Kader={row['total']} | "
                    f"Starter={row['starters']} | "
                    f"IN={row['sub_in']} | OUT={row['sub_out']}"
                )

            events = connection.execute(
                """
                SELECT
                    e.event_id,
                    e.team_id,
                    e.player_id,
                    e.minute,
                    et.code AS event_type,
                    p.first_name,
                    p.last_name,
                    t.name AS team_name
                FROM events e
                JOIN event_types et
                    ON et.event_type_id = e.event_type_id
                LEFT JOIN players p
                    ON p.player_id = e.player_id
                LEFT JOIN teams t
                    ON t.team_id = e.team_id
                WHERE
                    e.match_id = ?
                    AND et.code IN (
                        'SUBSTITUTION_IN',
                        'SUBSTITUTION_OUT'
                    )
                ORDER BY e.minute, e.event_id
                """,
                (match_id,),
            ).fetchall()

            print()
            print("WECHSEL-EVENTS")
            print("-" * 100)

            for row in events:
                marker = (
                    " <<< TEAM FEHLT"
                    if row["team_id"] is None
                    else ""
                )

                print(
                    f"{str(row['minute']):>3}' | "
                    f"{row['event_type']:<18} | "
                    f"team_id={str(row['team_id']):<4} | "
                    f"{str(row['team_name']):<30} | "
                    f"player_id={str(row['player_id']):<5} | "
                    f"{name(row)}"
                    f"{marker}"
                )

            if match_id == 260:
                print()
                print("TEAMLOSE WECHSEL: SPIELER-INDIZIEN")
                print("-" * 100)

                teamless = [
                    row
                    for row in events
                    if row["team_id"] is None
                ]

                for event in teamless:
                    player_id = event["player_id"]

                    player = connection.execute(
                        """
                        SELECT
                            p.player_id,
                            p.team_id,
                            p.first_name,
                            p.last_name,
                            t.name AS player_team
                        FROM players p
                        LEFT JOIN teams t
                            ON t.team_id = p.team_id
                        WHERE p.player_id = ?
                        """,
                        (player_id,),
                    ).fetchone()

                    lineup_team = connection.execute(
                        """
                        SELECT
                            l.team_id,
                            t.name AS team_name
                        FROM lineups l
                        LEFT JOIN teams t
                            ON t.team_id = l.team_id
                        WHERE
                            l.match_id = ?
                            AND l.player_id = ?
                        LIMIT 1
                        """,
                        (match_id, player_id),
                    ).fetchone()

                    print(
                        f"{event['event_type']} | "
                        f"{name(event)} | player_id={player_id}"
                    )
                    print(
                        "  players.team_id: "
                        f"{player['team_id'] if player else None} | "
                        f"{player['player_team'] if player else None}"
                    )
                    print(
                        "  lineup.team_id:  "
                        f"{lineup_team['team_id'] if lineup_team else None} | "
                        f"{lineup_team['team_name'] if lineup_team else None}"
                    )

            if match_id == 251:
                print()
                print("SPIEL 251: LINEUP-SPIELER")
                print("-" * 100)

                for row in lineups:
                    print(
                        f"{row['team_name']:<30} | "
                        f"starter={row['is_starting']} | "
                        f"player_id={row['player_id']} | "
                        f"{name(row)}"
                    )

        print()
        print("=" * 100)
        print("DIAGNOSE ENDE")
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
