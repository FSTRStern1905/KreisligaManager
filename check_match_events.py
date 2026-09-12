from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/database/kreisligamanager.db")

COMPETITION_NAME = "Kreisliga B11"
HOME_TEAM = "FSG Ehrang-Pfalzel"
AWAY_TEAM = "SG Pölich-Schleich"


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                m.match_id,
                m.matchday,
                m.match_date,
                m.kickoff_time,
                m.home_goals,
                m.away_goals,
                m.status,
                m.notes,
                c.competition_id,
                c.name AS competition_name,
                ht.team_id AS home_team_id,
                ht.name AS home_team_name,
                at.team_id AS away_team_id,
                at.name AS away_team_name
            FROM matches AS m
            INNER JOIN competitions AS c
                ON c.competition_id = m.competition_id
            INNER JOIN teams AS ht
                ON ht.team_id = m.home_team_id
            INNER JOIN teams AS at
                ON at.team_id = m.away_team_id
            WHERE
                c.name = ? COLLATE NOCASE
                AND ht.name = ? COLLATE NOCASE
                AND at.name = ? COLLATE NOCASE
            ORDER BY m.match_id DESC
            LIMIT 1
            """,
            (
                COMPETITION_NAME,
                HOME_TEAM,
                AWAY_TEAM,
            ),
        )

        match = cursor.fetchone()

        if match is None:
            raise RuntimeError("Spiel wurde nicht gefunden.")

        print("=" * 110)
        print("MATCH-/EVENT-CHECK")
        print("=" * 110)
        print(f"match_id:       {match['match_id']}")
        print(f"competition_id: {match['competition_id']}")
        print(f"Wettbewerb:     {match['competition_name']}")
        print(f"Spieltag:       {match['matchday']}")
        print(f"Datum:          {match['match_date']}")
        print(f"Anstoß:         {match['kickoff_time']}")
        print(
            f"Spiel:          {match['home_team_name']} "
            f"{match['home_goals']}:{match['away_goals']} "
            f"{match['away_team_name']}"
        )
        print(f"Status:         {match['status']}")
        print(f"Notizen:        {match['notes']}")
        print("=" * 110)

        cursor.execute(
            """
            SELECT
                e.event_id,
                et.code AS event_type,
                e.minute,
                e.team_id,
                t.name AS event_team,
                e.player_id,
                p.first_name,
                p.last_name
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            LEFT JOIN teams AS t
                ON t.team_id = e.team_id
            LEFT JOIN players AS p
                ON p.player_id = e.player_id
            WHERE e.match_id = ?
            ORDER BY
                CASE
                    WHEN e.minute IS NULL THEN 999
                    ELSE CAST(e.minute AS INTEGER)
                END,
                e.event_id
            """,
            (match["match_id"],),
        )

        events = cursor.fetchall()

        print()
        print(f"EVENTS GESAMT: {len(events)}")
        print("-" * 110)

        if not events:
            print("KEINE EVENTS FÜR DIESES SPIEL VORHANDEN.")
        else:
            for event in events:
                player_name = "—"

                if (
                    event["first_name"]
                    or event["last_name"]
                ):
                    player_name = " ".join(
                        part
                        for part in (
                            event["first_name"],
                            event["last_name"],
                        )
                        if part
                    )

                print(
                    f"event_id={event['event_id']:<7} | "
                    f"{str(event['event_type']):<20} | "
                    f"Min={str(event['minute']):<6} | "
                    f"team_id={str(event['team_id']):<5} | "
                    f"Team={str(event['event_team'] or '—'):<30} | "
                    f"player_id={str(event['player_id']):<6} | "
                    f"Spieler={player_name}"
                )

        cursor.execute(
            """
            SELECT
                et.code,
                COUNT(*) AS amount
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            WHERE e.match_id = ?
            GROUP BY et.code
            ORDER BY et.code
            """,
            (match["match_id"],),
        )

        counts = cursor.fetchall()

        print()
        print("EVENTTYPEN:")
        print("-" * 110)

        if not counts:
            print("Keine Eventtypen vorhanden.")
        else:
            for row in counts:
                print(
                    f"{row['code']:<25} {row['amount']}"
                )

        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
