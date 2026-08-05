from __future__ import annotations

import sqlite3

from src.services.validation.import_validation_service import (
    ImportValidationService,
)
from src.services.validation.validation_report import (
    ValidationReport,
)


DATABASE_PATH = (
    "data/database/kreisligamanager.db"
)


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        competition_row = connection.execute(
            """
            SELECT competition_id
            FROM competitions
            ORDER BY competition_id
            LIMIT 1;
            """
        ).fetchone()

        if competition_row is None:
            print(
                "Kein Wettbewerb gefunden."
            )
            return

        competition_id = int(
            competition_row[0]
        )

        validator = ImportValidationService(
            connection
        )

        result = validator.validate(
            competition_id=competition_id
        )

        report = ValidationReport()

        print(
            report.build_text(
                result
            )
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()