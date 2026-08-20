from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.validation.import_validation_service import (
    ImportValidationService,
)


DB_PATH = Path("data/database/kreisligamanager.db")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    try:
        service = ImportValidationService(
            connection
        )

        result = service.validate()

        print("=" * 70)
        print("VALIDATION-SMOKETEST")
        print("=" * 70)

        for check in result.checks:
            print()
            print(
                f"[{check.status}] {check.name}"
            )

            for message in check.errors:
                print(f"  FEHLER: {message}")

            for message in check.warnings:
                print(f"  WARNUNG: {message}")

        print()
        print("=" * 70)
        print("ZUSAMMENFASSUNG")
        print("=" * 70)
        print(
            f"PASS:      {result.passed_checks}"
        )
        print(
            f"WARNUNG:   {result.warning_checks}"
        )
        print(
            f"FEHLER:    {result.failed_checks}"
        )
        print(
            f"Warnungen: {result.warning_count}"
        )
        print(
            f"Fehler:    {result.error_count}"
        )
        print(
            f"is_valid:  {result.is_valid}"
        )

        print()

        if result.is_valid:
            print(
                "ERGEBNIS: VALIDIERUNG BLOCKIERT "
                "DEN COMMIT NICHT."
            )
        else:
            print(
                "ERGEBNIS: VALIDIERUNG WÜRDE "
                "DEN COMMIT NOCH BLOCKIEREN."
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
