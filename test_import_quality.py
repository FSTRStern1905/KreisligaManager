from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def get_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return {row[1] for row in rows}


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        print("=" * 60)
        print("IMPORT-QUALITÄTSCHECK")
        print("=" * 60)

        if not table_exists(connection, "players"):
            print("Tabelle 'players' nicht gefunden.")
            return

        columns = get_columns(connection, "players")

        id_col = (
            "player_id"
            if "player_id" in columns
            else "id"
        )

        first_name_col = (
            "first_name"
            if "first_name" in columns
            else None
        )

        last_name_col = (
            "last_name"
            if "last_name" in columns
            else None
        )

        external_id_col = (
            "external_id"
            if "external_id" in columns
            else None
        )

        team_id_col = (
            "team_id"
            if "team_id" in columns
            else None
        )

        total_players = connection.execute(
            "SELECT COUNT(*) FROM players"
        ).fetchone()[0]

        print(f"Spieler gesamt: {total_players}")

        if first_name_col and last_name_col:
            placeholder_count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM players
                WHERE LOWER(COALESCE({first_name_col}, '')) = 'unbekannt'
                   OR LOWER(COALESCE({last_name_col}, '')) LIKE 'unbekannt %'
                """
            ).fetchone()[0]

            empty_name_count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM players
                WHERE TRIM(COALESCE({first_name_col}, '')) = ''
                  AND TRIM(COALESCE({last_name_col}, '')) = ''
                """
            ).fetchone()[0]

            print(
                "Platzhalter-Spieler: "
                f"{placeholder_count}"
            )
            print(
                "Spieler ohne Namen: "
                f"{empty_name_count}"
            )

        if external_id_col:
            duplicate_external_ids = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT {external_id_col}
                    FROM players
                    WHERE NULLIF(
                        TRIM(COALESCE({external_id_col}, '')),
                        ''
                    ) IS NOT NULL
                    GROUP BY {external_id_col}
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]

            print(
                "Doppelte External-IDs: "
                f"{duplicate_external_ids}"
            )

        if first_name_col and last_name_col:
            group_columns = [
                f"LOWER(TRIM(COALESCE({first_name_col}, '')))",
                f"LOWER(TRIM(COALESCE({last_name_col}, '')))",
            ]

            if team_id_col:
                group_columns.insert(
                    0,
                    f"COALESCE({team_id_col}, -1)",
                )

            group_sql = ", ".join(group_columns)

            duplicate_names = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT {group_sql}
                    FROM players
                    WHERE TRIM(
                        COALESCE({first_name_col}, '') ||
                        COALESCE({last_name_col}, '')
                    ) <> ''
                    GROUP BY {group_sql}
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]

            print(
                "Doppelte Namen innerhalb Team: "
                f"{duplicate_names}"
            )

        print()
        print("BEISPIELE PLATZHALTER")
        print("-" * 60)

        if first_name_col and last_name_col:
            select_fields = [
                id_col,
                first_name_col,
                last_name_col,
            ]

            if external_id_col:
                select_fields.append(external_id_col)

            if team_id_col:
                select_fields.append(team_id_col)

            rows = connection.execute(
                f"""
                SELECT {", ".join(select_fields)}
                FROM players
                WHERE LOWER(
                    COALESCE({first_name_col}, '')
                ) = 'unbekannt'
                   OR LOWER(
                    COALESCE({last_name_col}, '')
                ) LIKE 'unbekannt %'
                ORDER BY {id_col}
                LIMIT 20
                """
            ).fetchall()

            if not rows:
                print("Keine Platzhalter gefunden.")
            else:
                for row in rows:
                    print(dict(row))

        print()
        print("=" * 60)
        print("CHECK ABGESCHLOSSEN")
        print("=" * 60)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
