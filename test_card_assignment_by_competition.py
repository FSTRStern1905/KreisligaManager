from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")

CARD_CODES = (
    "YELLOW_CARD",
    "YELLOW_RED_CARD",
    "RED_CARD",
)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        competitions = connection.execute(
            """
            SELECT
                competition_id,
                name
            FROM competitions
            ORDER BY competition_id
            """
        ).fetchall()

        print("=" * 78)
        print("KARTEN-CHECK PRO WETTBEWERB")
        print("=" * 78)

        if not competitions:
            print("Keine Wettbewerbe gefunden.")
            return

        for competition in competitions:
            competition_id = int(
                competition["competition_id"]
            )
            competition_name = str(
                competition["name"]
            )

            print()
            print("=" * 78)
            print(
                f"{competition_name} "
                f"(competition_id={competition_id})"
            )
            print("=" * 78)

            rows = connection.execute(
                """
                SELECT
                    et.code AS event_type_code,
                    COUNT(*) AS event_count,
                    SUM(
                        CASE
                            WHEN e.player_id IS NOT NULL
                            THEN 1
                            ELSE 0
                        END
                    ) AS assigned_count,
                    SUM(
                        CASE
                            WHEN e.player_id IS NULL
                            THEN 1
                            ELSE 0
                        END
                    ) AS unassigned_count
                FROM events AS e
                INNER JOIN event_types AS et
                    ON et.event_type_id =
                       e.event_type_id
                INNER JOIN matches AS m
                    ON m.match_id = e.match_id
                WHERE
                    m.competition_id = ?
                    AND et.code IN (
                        'YELLOW_CARD',
                        'YELLOW_RED_CARD',
                        'RED_CARD'
                    )
                GROUP BY et.code
                ORDER BY et.code
                """,
                (competition_id,),
            ).fetchall()

            by_code = {
                str(row["event_type_code"]): row
                for row in rows
            }

            total_cards = 0
            total_unassigned = 0

            for code in CARD_CODES:
                row = by_code.get(code)

                event_count = (
                    int(row["event_count"])
                    if row is not None
                    else 0
                )
                assigned_count = (
                    int(row["assigned_count"] or 0)
                    if row is not None
                    else 0
                )
                unassigned_count = (
                    int(row["unassigned_count"] or 0)
                    if row is not None
                    else 0
                )

                total_cards += event_count
                total_unassigned += (
                    unassigned_count
                )

                rate = (
                    assigned_count
                    / event_count
                    * 100
                    if event_count
                    else 100.0
                )

                print(
                    f"{code:<18} "
                    f"Events={event_count:<5} "
                    f"zugeordnet={assigned_count:<5} "
                    f"ohne Spieler={unassigned_count:<5} "
                    f"Quote={rate:6.2f}%"
                )

            print("-" * 78)
            print(
                f"Karten gesamt: {total_cards}"
            )
            print(
                "Ohne Spielerzuordnung: "
                f"{total_unassigned}"
            )

            if total_unassigned == 0:
                print(
                    "STATUS: OK - alle Karten "
                    "haben eine Spielerzuordnung."
                )
            else:
                print(
                    "STATUS: WARNUNG - Karten "
                    "ohne Spielerzuordnung vorhanden."
                )

                examples = connection.execute(
                    """
                    SELECT
                        m.matchday,
                        ht.name AS home_team,
                        at.name AS away_team,
                        et.code AS event_type_code,
                        e.minute,
                        e.notes
                    FROM events AS e
                    INNER JOIN event_types AS et
                        ON et.event_type_id =
                           e.event_type_id
                    INNER JOIN matches AS m
                        ON m.match_id = e.match_id
                    INNER JOIN teams AS ht
                        ON ht.team_id =
                           m.home_team_id
                    INNER JOIN teams AS at
                        ON at.team_id =
                           m.away_team_id
                    WHERE
                        m.competition_id = ?
                        AND et.code IN (
                            'YELLOW_CARD',
                            'YELLOW_RED_CARD',
                            'RED_CARD'
                        )
                        AND e.player_id IS NULL
                    ORDER BY
                        m.matchday,
                        m.match_id,
                        e.minute
                    LIMIT 20
                    """,
                    (competition_id,),
                ).fetchall()

                print()
                print(
                    "Beispiele ohne Spielerzuordnung:"
                )

                for row in examples:
                    print(
                        f"  ST {row['matchday']} | "
                        f"{row['home_team']} - "
                        f"{row['away_team']} | "
                        f"{row['event_type_code']} | "
                        f"{row['minute']}' | "
                        f"{row['notes']}"
                    )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
