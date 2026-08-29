from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")

MATCH_IDS = (
    184,
    185,
    188,
)


def full_name(
    first_name: str | None,
    last_name: str | None,
) -> str:
    return " ".join(
        part
        for part in (
            first_name or "",
            last_name or "",
        )
        if part
    ) or "?"


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        print("=" * 92)
        print("PLAYER_MATCH_STATS ↔ EVENT PLAYER-ID DIAGNOSE")
        print("=" * 92)

        for match_id in MATCH_IDS:
            match = connection.execute(
                """
                SELECT
                    m.match_id,
                    m.matchday,
                    ht.name AS home_team,
                    at.name AS away_team
                FROM matches AS m
                INNER JOIN teams AS ht
                    ON ht.team_id = m.home_team_id
                INNER JOIN teams AS at
                    ON at.team_id = m.away_team_id
                WHERE m.match_id = ?
                """,
                (match_id,),
            ).fetchone()

            if match is None:
                print()
                print(
                    f"Spiel {match_id} nicht gefunden."
                )
                continue

            print()
            print("=" * 92)
            print(
                f"Spiel {match_id} | "
                f"ST {match['matchday']} | "
                f"{match['home_team']} - "
                f"{match['away_team']}"
            )
            print("=" * 92)

            event_players = connection.execute(
                """
                SELECT DISTINCT
                    e.team_id,
                    e.player_id,
                    p.first_name,
                    p.last_name,
                    et.code AS event_type
                FROM events AS e
                INNER JOIN event_types AS et
                    ON et.event_type_id =
                       e.event_type_id
                LEFT JOIN players AS p
                    ON p.player_id = e.player_id
                WHERE
                    e.match_id = ?
                    AND et.code IN (
                        'SUBSTITUTION_IN',
                        'SUBSTITUTION_OUT'
                    )
                    AND e.player_id IS NOT NULL
                ORDER BY
                    e.team_id,
                    e.player_id,
                    et.code
                """,
                (match_id,),
            ).fetchall()

            for row in event_players:
                player_id = int(
                    row["player_id"]
                )

                lineup = connection.execute(
                    """
                    SELECT
                        lineup_id,
                        team_id,
                        is_starting,
                        shirt_number
                    FROM lineups
                    WHERE
                        match_id = ?
                        AND player_id = ?
                    """,
                    (
                        match_id,
                        player_id,
                    ),
                ).fetchall()

                stats = connection.execute(
                    """
                    SELECT
                        player_match_stat_id,
                        team_id,
                        is_starting,
                        was_substituted_in,
                        was_substituted_out,
                        minute_in,
                        minute_out
                    FROM player_match_stats
                    WHERE
                        match_id = ?
                        AND player_id = ?
                    """,
                    (
                        match_id,
                        player_id,
                    ),
                ).fetchall()

                status = "OK"

                if not lineup:
                    status = "FEHLT IN LINEUP"
                elif not stats:
                    status = "FEHLT IN STATS"
                elif (
                    row["event_type"]
                    == "SUBSTITUTION_IN"
                    and not any(
                        item[
                            "was_substituted_in"
                        ]
                        for item in stats
                    )
                ):
                    status = "IN-FLAG FEHLT"
                elif (
                    row["event_type"]
                    == "SUBSTITUTION_OUT"
                    and not any(
                        item[
                            "was_substituted_out"
                        ]
                        for item in stats
                    )
                ):
                    status = "OUT-FLAG FEHLT"

                if status == "OK":
                    continue

                print()
                print(
                    f"[{status}] "
                    f"{full_name(row['first_name'], row['last_name'])}"
                )
                print(
                    f"  player_id:  {player_id}"
                )
                print(
                    f"  team_id:    {row['team_id']}"
                )
                print(
                    f"  Event:      {row['event_type']}"
                )
                print(
                    f"  Lineuprows: {len(lineup)}"
                )
                print(
                    f"  Statsrows:  {len(stats)}"
                )

                for item in lineup:
                    print(
                        "    LINEUP "
                        f"id={item['lineup_id']} "
                        f"team={item['team_id']} "
                        f"starter={item['is_starting']} "
                        f"nr={item['shirt_number']}"
                    )

                for item in stats:
                    print(
                        "    STATS  "
                        f"id={item['player_match_stat_id']} "
                        f"team={item['team_id']} "
                        f"starter={item['is_starting']} "
                        f"in={item['was_substituted_in']} "
                        f"out={item['was_substituted_out']} "
                        f"min_in={item['minute_in']} "
                        f"min_out={item['minute_out']}"
                    )

        print()
        print("=" * 92)
        print("DIAGNOSE ENDE")
        print("=" * 92)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
