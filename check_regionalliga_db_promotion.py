from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path


MAIN_DB = Path(
    "data/database/kreisligamanager.db"
)

FINAL_DB = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)

REGIONALLIGA_NAME = "Regionalliga Südwest"


def get_tables(
    connection: sqlite3.Connection,
) -> list[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE
            type = 'table'
            AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    return [
        str(row[0])
        for row in rows
    ]


def get_columns(
    connection: sqlite3.Connection,
    table: str,
) -> list[str]:
    rows = connection.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    return [
        str(row[1])
        for row in rows
    ]


def get_primary_key_columns(
    connection: sqlite3.Connection,
    table: str,
) -> list[str]:
    rows = connection.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    pk_rows = [
        row
        for row in rows
        if int(row[5] or 0) > 0
    ]

    pk_rows.sort(
        key=lambda row: int(row[5])
    )

    return [
        str(row[1])
        for row in pk_rows
    ]


def quote_identifier(
    value: str,
) -> str:
    return (
        '"'
        + value.replace('"', '""')
        + '"'
    )


def fetch_all_rows(
    connection: sqlite3.Connection,
    table: str,
    columns: list[str],
) -> list[tuple]:
    column_sql = ", ".join(
        quote_identifier(column)
        for column in columns
    )

    return connection.execute(
        f"""
        SELECT {column_sql}
        FROM {quote_identifier(table)}
        """
    ).fetchall()


def build_row_map(
    rows: list[tuple],
    columns: list[str],
    pk_columns: list[str],
) -> dict[tuple, tuple]:
    column_index = {
        column: index
        for index, column in enumerate(
            columns
        )
    }

    result: dict[tuple, tuple] = {}

    for row in rows:
        key = tuple(
            row[
                column_index[pk_column]
            ]
            for pk_column in pk_columns
        )
        result[key] = tuple(row)

    return result


def compare_table(
    main_connection: sqlite3.Connection,
    final_connection: sqlite3.Connection,
    table: str,
) -> dict:
    main_columns = get_columns(
        main_connection,
        table,
    )
    final_columns = get_columns(
        final_connection,
        table,
    )

    if main_columns != final_columns:
        return {
            "table": table,
            "status": "SCHEMA_DIFFERENT",
            "main_count": None,
            "final_count": None,
            "missing_in_final": None,
            "changed_in_final": None,
            "extra_in_final": None,
            "details": (
                f"Spalten unterscheiden sich. "
                f"MAIN={main_columns} | "
                f"FINAL={final_columns}"
            ),
        }

    pk_columns = get_primary_key_columns(
        main_connection,
        table,
    )

    main_rows = fetch_all_rows(
        main_connection,
        table,
        main_columns,
    )
    final_rows = fetch_all_rows(
        final_connection,
        table,
        final_columns,
    )

    if pk_columns:
        main_map = build_row_map(
            main_rows,
            main_columns,
            pk_columns,
        )
        final_map = build_row_map(
            final_rows,
            final_columns,
            pk_columns,
        )

        missing_keys = [
            key
            for key in main_map
            if key not in final_map
        ]

        changed_keys = [
            key
            for key in main_map
            if (
                key in final_map
                and main_map[key]
                != final_map[key]
            )
        ]

        extra_keys = [
            key
            for key in final_map
            if key not in main_map
        ]

        return {
            "table": table,
            "status": (
                "OK"
                if (
                    not missing_keys
                    and not changed_keys
                )
                else "DIFFERENT"
            ),
            "main_count": len(main_rows),
            "final_count": len(final_rows),
            "missing_in_final": len(
                missing_keys
            ),
            "changed_in_final": len(
                changed_keys
            ),
            "extra_in_final": len(
                extra_keys
            ),
            "details": {
                "missing_examples": (
                    missing_keys[:5]
                ),
                "changed_examples": (
                    changed_keys[:5]
                ),
                "extra_examples": (
                    extra_keys[:5]
                ),
            },
        }

    main_counter = Counter(
        tuple(row)
        for row in main_rows
    )
    final_counter = Counter(
        tuple(row)
        for row in final_rows
    )

    missing_count = sum(
        (
            main_counter
            - final_counter
        ).values()
    )

    extra_count = sum(
        (
            final_counter
            - main_counter
        ).values()
    )

    return {
        "table": table,
        "status": (
            "OK"
            if missing_count == 0
            else "DIFFERENT"
        ),
        "main_count": len(main_rows),
        "final_count": len(final_rows),
        "missing_in_final": (
            missing_count
        ),
        "changed_in_final": 0,
        "extra_in_final": extra_count,
        "details": {},
    }


def competition_summary(
    connection: sqlite3.Connection,
) -> list[dict]:
    tables = set(
        get_tables(
            connection
        )
    )

    if "competitions" not in tables:
        return []

    columns = set(
        get_columns(
            connection,
            "competitions",
        )
    )

    select_parts = [
        "competition_id",
        "name",
    ]

    for optional in (
        "season_id",
        "league_id",
        "external_id",
    ):
        if optional in columns:
            select_parts.append(
                optional
            )

    sql = (
        "SELECT "
        + ", ".join(select_parts)
        + " FROM competitions "
        + "ORDER BY competition_id"
    )

    connection.row_factory = sqlite3.Row

    return [
        dict(row)
        for row in connection.execute(
            sql
        ).fetchall()
    ]


def regionalliga_present(
    connection: sqlite3.Connection,
) -> bool:
    tables = set(
        get_tables(
            connection
        )
    )

    if "competitions" not in tables:
        return False

    row = connection.execute(
        """
        SELECT 1
        FROM competitions
        WHERE name = ?
        LIMIT 1
        """,
        (REGIONALLIGA_NAME,),
    ).fetchone()

    return row is not None


def main() -> None:
    print("=" * 110)
    print(
        "REGIONALLIGA-DATENBANK PROMOTION "
        "- SICHERHEITSPRÜFUNG"
    )
    print("=" * 110)
    print(f"Haupt-DB: {MAIN_DB}")
    print(f"Final-DB: {FINAL_DB}")
    print(
        "Dieser Test verändert KEINE Datenbank."
    )

    if not MAIN_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {MAIN_DB}"
        )

    if not FINAL_DB.exists():
        raise FileNotFoundError(
            f"Final-Test-DB fehlt: {FINAL_DB}"
        )

    main_connection = sqlite3.connect(
        MAIN_DB
    )
    final_connection = sqlite3.connect(
        FINAL_DB
    )

    try:
        main_tables = get_tables(
            main_connection
        )
        final_tables = get_tables(
            final_connection
        )

        print()
        print("=" * 110)
        print("SCHEMA")
        print("=" * 110)
        print(
            f"Tabellen Haupt-DB: "
            f"{len(main_tables)}"
        )
        print(
            f"Tabellen Final-DB: "
            f"{len(final_tables)}"
        )

        missing_tables = sorted(
            set(main_tables)
            - set(final_tables)
        )

        extra_tables = sorted(
            set(final_tables)
            - set(main_tables)
        )

        print(
            f"Fehlen in Final-DB: "
            f"{missing_tables or '(keine)'}"
        )
        print(
            f"Zusätzlich in Final-DB: "
            f"{extra_tables or '(keine)'}"
        )

        print()
        print("=" * 110)
        print("WETTBEWERBE HAUPT-DB")
        print("=" * 110)

        for row in competition_summary(
            main_connection
        ):
            print(row)

        print()
        print("=" * 110)
        print("WETTBEWERBE FINAL-DB")
        print("=" * 110)

        for row in competition_summary(
            final_connection
        ):
            print(row)

        print()
        print("=" * 110)
        print("TABELLENVERGLEICH")
        print("=" * 110)

        results: list[dict] = []

        for table in main_tables:
            if table not in final_tables:
                continue

            result = compare_table(
                main_connection,
                final_connection,
                table,
            )
            results.append(
                result
            )

            print(
                f"{table:<32} "
                f"{result['status']:<18} "
                f"MAIN={result['main_count']} | "
                f"FINAL={result['final_count']} | "
                f"fehlt={result['missing_in_final']} | "
                f"geändert={result['changed_in_final']} | "
                f"zusätzlich={result['extra_in_final']}"
            )

            if (
                result["status"]
                != "OK"
            ):
                print(
                    f"  DETAILS: "
                    f"{result['details']}"
                )

        unsafe_results = [
            result
            for result in results
            if result["status"] != "OK"
        ]

        main_has_regionalliga = (
            regionalliga_present(
                main_connection
            )
        )

        final_has_regionalliga = (
            regionalliga_present(
                final_connection
            )
        )

        print()
        print("=" * 110)
        print("GESAMTERGEBNIS")
        print("=" * 110)
        print(
            "Regionalliga in Haupt-DB: "
            f"{main_has_regionalliga}"
        )
        print(
            "Regionalliga in Final-DB: "
            f"{final_has_regionalliga}"
        )
        print(
            "Tabellen mit fehlenden/geänderten "
            f"Haupt-DB-Zeilen: "
            f"{len(unsafe_results)}"
        )

        safe = (
            not missing_tables
            and not unsafe_results
            and final_has_regionalliga
        )

        if safe:
            print()
            print(
                "STATUS: SICHER FÜR PROMOTION."
            )
            print(
                "Die Final-Test-DB enthält alle "
                "Zeilen der aktuellen Haupt-DB "
                "unverändert und zusätzlich die "
                "Regionalliga-Daten."
            )
            print(
                "Damit kann die Haupt-DB nach "
                "Backup durch die Final-Test-DB "
                "ersetzt werden."
            )
        else:
            print()
            print(
                "STATUS: NICHT AUTOMATISCH ERSETZEN."
            )
            print(
                "Die Datenbanken unterscheiden sich "
                "bei bereits vorhandenen Daten. "
                "Dann müssen wir gezielt mergen, "
                "statt die Datei zu ersetzen."
            )

        print("=" * 110)

    finally:
        main_connection.close()
        final_connection.close()


if __name__ == "__main__":
    main()
