from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(r"E:\\Kreisligamanager")

TABLES_TO_CHECK = (
    "matches",
    "events",
    "lineups",
    "player_match_stats",
)


def get_table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    return {str(row[0]) for row in rows}


def get_count(
    connection: sqlite3.Connection,
    table: str,
    tables: set[str],
) -> int | str:
    if table not in tables:
        return "-"

    return int(
        connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    )


def main() -> None:
    database_files = sorted(
        PROJECT_ROOT.rglob("*.db"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    print("=" * 100)
    print("DIAGNOSE DATENBANK-STANDORTE")
    print("=" * 100)
    print(f"Projekt: {PROJECT_ROOT}")
    print(f"Gefundene .db-Dateien: {len(database_files)}")
    print()

    if not database_files:
        print("Keine Datenbankdateien gefunden.")
        return

    for index, db_path in enumerate(database_files, start=1):
        print("=" * 100)
        print(f"{index}. {db_path}")
        print("-" * 100)

        stat = db_path.stat()
        print(f"Größe: {stat.st_size:,} Bytes")

        try:
            connection = sqlite3.connect(db_path)
            tables = get_table_names(connection)

            for table in TABLES_TO_CHECK:
                count = get_count(
                    connection,
                    table,
                    tables,
                )
                print(f"{table:<22}: {count}")

            connection.close()

        except Exception as exc:
            print(f"FEHLER: {exc}")

        print()

    print("=" * 100)
    print("ERGEBNIS")
    print("=" * 100)
    print(
        "Die Datenbank mit den importierten Spielen ist die Datei, "
        "bei der matches/events/lineups/player_match_stats nicht 0 sind."
    )
    print("=" * 100)


if __name__ == "__main__":
    main()
