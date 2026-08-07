from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/database/kreisligamanager.db")
MATCH_EXTERNAL_ID = "02TKDR1R3C000000VS5489BUVUD1610F"
TARGET_EXTERNAL_ID = "02ODNC1NIS000000VS5489B5VVTGIU9E"
TARGET_NAME = "Bahoya"


def sep(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        match = connection.execute(
            """
            SELECT match_id
            FROM matches
            WHERE external_id = ?
            LIMIT 1;
            """,
            (MATCH_EXTERNAL_ID,),
        ).fetchone()

        if match is None:
            print("Spiel nicht gefunden.")
            return

        match_id = int(match[0])

        sep("BAHOYA – SPIELERDATENBANK")

        players = connection.execute(
            """
            SELECT
                player_id,
                first_name,
                last_name,
                external_id,
                team_id
            FROM players
            WHERE
                external_id = ?
                OR first_name LIKE ?
                OR last_name LIKE ?
            ORDER BY player_id;
            """,
            (
                TARGET_EXTERNAL_ID,
                f"%{TARGET_NAME}%",
                f"%{TARGET_NAME}%",
            ),
        ).fetchall()

        for row in players:
            print(row)

        sep("BAHOYA – LINEUP VON SPIEL 3")

        lineup_rows = connection.execute(
            """
            SELECT
                l.lineup_id,
                l.player_id,
                p.first_name,
                p.last_name,
                p.external_id,
                l.team_id,
                t.name,
                l.is_starting,
                l.shirt_number,
                l.position
            FROM lineups l
            INNER JOIN players p
                ON p.player_id = l.player_id
            LEFT JOIN teams t
                ON t.team_id = l.team_id
            WHERE
                l.match_id = ?
                AND (
                    p.external_id = ?
                    OR p.first_name LIKE ?
                    OR p.last_name LIKE ?
                )
            ORDER BY l.lineup_id;
            """,
            (
                match_id,
                TARGET_EXTERNAL_ID,
                f"%{TARGET_NAME}%",
                f"%{TARGET_NAME}%",
            ),
        ).fetchall()

        if not lineup_rows:
            print("KEIN BAHOYA-EINTRAG IN LINEUPS.")
        else:
            for row in lineup_rows:
                print(row)

        sep("EVENTS VON BAHOYA")

        event_rows = connection.execute(
            """
            SELECT
                e.event_id,
                e.player_id,
                p.first_name,
                p.last_name,
                p.external_id,
                et.code,
                e.minute,
                e.team_id,
                t.name
            FROM events e
            INNER JOIN event_types et
                ON et.event_type_id = e.event_type_id
            LEFT JOIN players p
                ON p.player_id = e.player_id
            LEFT JOIN teams t
                ON t.team_id = e.team_id
            WHERE
                e.match_id = ?
                AND (
                    p.external_id = ?
                    OR p.first_name LIKE ?
                    OR p.last_name LIKE ?
                )
            ORDER BY e.minute, e.event_id;
            """,
            (
                match_id,
                TARGET_EXTERNAL_ID,
                f"%{TARGET_NAME}%",
                f"%{TARGET_NAME}%",
            ),
        ).fetchall()

        for row in event_rows:
            print(row)

        sep("GESAMTE FRANKFURT-LINEUP")

        frankfurt_rows = connection.execute(
            """
            SELECT
                l.lineup_id,
                l.player_id,
                p.first_name,
                p.last_name,
                p.external_id,
                l.is_starting,
                l.shirt_number
            FROM lineups l
            INNER JOIN players p
                ON p.player_id = l.player_id
            INNER JOIN teams t
                ON t.team_id = l.team_id
            WHERE
                l.match_id = ?
                AND t.name = 'Eintracht Frankfurt'
            ORDER BY
                l.is_starting DESC,
                l.lineup_id;
            """,
            (match_id,),
        ).fetchall()

        for row in frankfurt_rows:
            print(row)

        sep("ERGEBNIS")

        if not lineup_rows:
            print(
                "Bahoya fehlt bereits in der lineups-Tabelle. "
                "Der Fehler liegt damit VOR dem PlayerMatchStatsBuilder "
                "(LineupParser/LineupImporter)."
            )
        else:
            lineup_player_ids = {
                int(row[1])
                for row in lineup_rows
            }

            event_player_ids = {
                int(row[1])
                for row in event_rows
                if row[1] is not None
            }

            print(
                f"Lineup player_ids: {sorted(lineup_player_ids)}"
            )
            print(
                f"Event player_ids:  {sorted(event_player_ids)}"
            )

            if lineup_player_ids != event_player_ids:
                print(
                    "TREFFER: Bahoya existiert in Lineup und Events "
                    "unter unterschiedlichen player_ids."
                )
            else:
                print(
                    "Bahoya besitzt dieselbe player_id in Lineup und Events. "
                    "Dann prüfen wir als Nächstes LineupMapper."
                )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
