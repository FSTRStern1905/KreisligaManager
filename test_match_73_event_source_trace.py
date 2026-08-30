from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

MATCH_ID = 73
TARGET_MINUTES = (
    71,
    86,
)


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 73 / EVENT-QUELLEN-TRACE "
        "71' UND 86'"
    )
    print("=" * 110)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank fehlt: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        print(
            f"Datenbank: {DB_PATH}"
        )
        print(
            "Haupt-DB wird NICHT verändert."
        )

        columns = [
            row["name"]
            for row in connection.execute(
                """
                PRAGMA table_info(events)
                """
            ).fetchall()
        ]

        print()
        print("EVENTS-SPALTEN")
        print("-" * 110)
        print(columns)

        select_columns = [
            "e.event_id",
            "et.code",
            "e.minute",
            "e.second",
            "e.team_id",
            "e.player_id",
            "p.first_name",
            "p.last_name",
            "e.related_player_id",
            "rp.first_name AS related_first_name",
            "rp.last_name AS related_last_name",
        ]

        if "value" in columns:
            select_columns.append(
                "e.value"
            )

        if "notes" in columns:
            select_columns.append(
                "e.notes"
            )

        if "created_at" in columns:
            select_columns.append(
                "e.created_at"
            )

        query = f"""
            SELECT
                {", ".join(select_columns)}
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            LEFT JOIN players AS p
                ON p.player_id = e.player_id
            LEFT JOIN players AS rp
                ON rp.player_id = e.related_player_id
            WHERE
                e.match_id = ?
                AND e.minute IN (?, ?)
            ORDER BY
                e.minute,
                e.event_id
        """

        rows = connection.execute(
            query,
            (
                MATCH_ID,
                *TARGET_MINUTES,
            ),
        ).fetchall()

        print()
        print("EVENTS 71' / 86'")
        print("=" * 110)

        for row in rows:
            data = dict(row)

            print()
            print("-" * 110)
            print(
                f"EVENT {data['event_id']} | "
                f"{data['minute']}' | "
                f"{data['code']}"
            )
            print("-" * 110)

            for key, value in data.items():
                print(
                    f"{key}: {value}"
                )

        print()
        print("=" * 110)
        print("QUELLEN-ZUSAMMENFASSUNG")
        print("=" * 110)

        if "value" not in columns:
            print(
                "Die events-Tabelle besitzt keine "
                "value-Spalte."
            )
            return

        for minute in TARGET_MINUTES:
            minute_rows = [
                row
                for row in rows
                if int(
                    row["minute"]
                ) == minute
            ]

            print()
            print(
                f"{minute}'"
            )
            print("-" * 110)

            if not minute_rows:
                print("(keine Events)")
                continue

            for row in minute_rows:
                value = str(
                    row["value"]
                    or ""
                )

                source = "unbekannt"

                if (
                    "source:liveticker"
                    in value.casefold()
                ):
                    source = "liveticker"

                elif (
                    "source:match_html"
                    in value.casefold()
                    or "source:html"
                    in value.casefold()
                ):
                    source = "match_html"

                elif (
                    "substitution_"
                    in value.casefold()
                ):
                    source = (
                        "Substitution ohne "
                        "expliziten Source-Tag"
                    )

                print(
                    f"event_id={row['event_id']} | "
                    f"{row['code']} | "
                    f"Quelle={source} | "
                    f"value={value!r}"
                )

        print()
        print("=" * 110)
        print("BEFUND")
        print("=" * 110)
        print(
            "Wenn die 71'-Events einen anderen "
            "Source-Tag als die 86'-Events tragen, "
            "haben wir zwei Importquellen gemischt."
        )
        print(
            "Wenn beide denselben Source-Tag tragen, "
            "liegt der Fehler in einer älteren "
            "HTML-/Parser-Zuordnung oder einem "
            "historischen Importbestand."
        )
        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
