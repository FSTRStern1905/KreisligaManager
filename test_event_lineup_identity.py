from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")

MATCH_IDS = (
    184,
    185,
    188,
)


def normalize(value: str | None) -> str:
    return " ".join(
        (value or "").casefold().split()
    )


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        print("=" * 96)
        print("EVENT-SPIELER ↔ LINEUP-IDENTITÄTSCHECK")
        print("=" * 96)

        for match_id in MATCH_IDS:
            match = connection.execute(
                """
                SELECT
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
                continue

            print()
            print("=" * 96)
            print(
                f"Spiel {match_id} | "
                f"ST {match['matchday']} | "
                f"{match['home_team']} - "
                f"{match['away_team']}"
            )
            print("=" * 96)

            event_players = connection.execute(
                """
                SELECT DISTINCT
                    e.player_id,
                    e.team_id,
                    p.external_id,
                    p.first_name,
                    p.last_name
                FROM events AS e
                INNER JOIN event_types AS et
                    ON et.event_type_id = e.event_type_id
                INNER JOIN players AS p
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
                    e.player_id
                """,
                (match_id,),
            ).fetchall()

            for event_player in event_players:
                player_id = int(
                    event_player["player_id"]
                )
                team_id = event_player["team_id"]

                direct_lineup = connection.execute(
                    """
                    SELECT lineup_id
                    FROM lineups
                    WHERE
                        match_id = ?
                        AND player_id = ?
                    LIMIT 1
                    """,
                    (
                        match_id,
                        player_id,
                    ),
                ).fetchone()

                if direct_lineup is not None:
                    continue

                first_name = str(
                    event_player["first_name"]
                    or ""
                )
                last_name = str(
                    event_player["last_name"]
                    or ""
                )

                lineup_players = connection.execute(
                    """
                    SELECT
                        l.player_id,
                        l.team_id,
                        l.is_starting,
                        p.external_id,
                        p.first_name,
                        p.last_name
                    FROM lineups AS l
                    INNER JOIN players AS p
                        ON p.player_id = l.player_id
                    WHERE
                        l.match_id = ?
                        AND (
                            l.team_id = ?
                            OR ? IS NULL
                        )
                    """,
                    (
                        match_id,
                        team_id,
                        team_id,
                    ),
                ).fetchall()

                same_name = [
                    row
                    for row in lineup_players
                    if (
                        normalize(
                            row["first_name"]
                        )
                        == normalize(first_name)
                        and normalize(
                            row["last_name"]
                        )
                        == normalize(last_name)
                    )
                ]

                print()
                print(
                    f"EVENT: {first_name} {last_name}"
                )
                print(
                    f"  event player_id:   {player_id}"
                )
                print(
                    "  event external_id: "
                    f"{event_player['external_id']}"
                )
                print(
                    f"  event team_id:     {team_id}"
                )

                if same_name:
                    print(
                        "  >>> GLEICHER NAME IN LINEUP "
                        "MIT ANDERER ID:"
                    )

                    for row in same_name:
                        print(
                            "      lineup player_id="
                            f"{row['player_id']} | "
                            "external_id="
                            f"{row['external_id']} | "
                            "team_id="
                            f"{row['team_id']} | "
                            "starter="
                            f"{row['is_starting']}"
                        )
                else:
                    print(
                        "  >>> NAME KOMMT IN LINEUP "
                        "ÜBERHAUPT NICHT VOR."
                    )

        print()
        print("=" * 96)
        print("CHECK ENDE")
        print("=" * 96)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
