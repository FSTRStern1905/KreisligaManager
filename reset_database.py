from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.database_reset_service import (
    DatabaseResetService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


def print_preview(
    preview: dict,
) -> None:
    print()
    print("=" * 60)
    print("DATENBANK-ZURÜCKSETZUNG")
    print("=" * 60)

    print(
        f"Datenbank: {DATABASE_PATH}"
    )

    print()
    print("Zu löschende Datensätze:")

    for table_name, count in preview[
        "counts"
    ].items():
        print(
            f"- {table_name}: {count}"
        )

    print()
    print(
        "Gesamt:",
        preview["total_rows"],
    )

    print()
    print(
        "Beibehalten:",
        ", ".join(
            preview["preserved_tables"]
        ),
    )


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "Die Datenbank wurde nicht gefunden: "
            f"{DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        service = DatabaseResetService(
            connection
        )

        preview = service.preview()

        print_preview(
            preview
        )

        if preview["total_rows"] == 0:
            print()
            print(
                "Die Datenbank enthält keine "
                "zu löschenden Datensätze."
            )
            return

        print()
        confirmation = input(
            "Zum vollständigen Zurücksetzen "
            "'RESET' eingeben: "
        ).strip()

        if confirmation != "RESET":
            print()
            print(
                "Zurücksetzen abgebrochen."
            )
            return

        result = service.reset()

        print()
        print("=" * 60)
        print("DATENBANK ZURÜCKGESETZT")
        print("=" * 60)

        print(
            "Tabellen geleert:",
            result["tables_reset"],
        )

        print(
            "Datensätze gelöscht:",
            result["rows_deleted"],
        )

        print(
            "Beibehalten:",
            ", ".join(
                result["preserved_tables"]
            ),
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()