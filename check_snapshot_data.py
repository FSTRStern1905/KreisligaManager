from __future__ import annotations

from src.database.database import Database


MATCH_EXTERNAL_ID = (
    "02TNB07C34000000VS5489BUVSSD35NB"
)


def main() -> None:
    database = Database(
        database_name="kreisligamanager_test.db",
    )

    connection = database.connect()

    try:
        match_row = connection.execute(
            """
            SELECT
                match_id,
                notes,
                home_goals,
                away_goals,
                stadium_id,
                referee_id,
                attendance
            FROM matches
            WHERE external_id = ?
            LIMIT 1
            """,
            (MATCH_EXTERNAL_ID,),
        ).fetchone()

        if match_row is None:
            print("Spiel wurde nicht gefunden.")
            return

        match_id = int(
            match_row["match_id"]
        )

        lineup_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM lineups
            WHERE match_id = ?
            """,
            (match_id,),
        ).fetchone()[0]

        player_count = connection.execute(
            """
            SELECT COUNT(DISTINCT player_id)
            FROM events
            WHERE
                match_id = ?
                AND player_id IS NOT NULL
            """,
            (match_id,),
        ).fetchone()[0]

        print()
        print("=" * 60)
        print("SNAPSHOT-DATENBANKPRÜFUNG")
        print("=" * 60)
        print(f"Interne Spiel-ID: {match_id}")
        print(
            f"Ergebnis: "
            f"{match_row['home_goals']}:"
            f"{match_row['away_goals']}"
        )
        print(f"Notizen: {match_row['notes']!r}")
        print(f"Stadion-ID: {match_row['stadium_id']}")
        print(f"Schiedsrichter-ID: {match_row['referee_id']}")
        print(f"Zuschauer: {match_row['attendance']}")
        print(f"Aufstellungseinträge: {lineup_count}")
        print(f"Spieler über Events: {player_count}")

    finally:
        database.close()


if __name__ == "__main__":
    main()