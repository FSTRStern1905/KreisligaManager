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
        # Test-Wettbewerb
        competition_id = 7

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