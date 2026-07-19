from pathlib import Path

from src.database.repository import Repository
from src.importer.csv_importer import CSVImporter
from src.importer.club_import_service import ClubImportService


class ClubImporter(CSVImporter):
    REQUIRED_COLUMNS = [
        "club_id",
        "club_name",
        "club_short_name",
        "association",
        "country",
        "founded",
        "city",
        "website",
        "logo",
    ]

    def __init__(
        self,
        repository: Repository,
        file_path: str | Path,
    ):
        super().__init__(
            file_path=file_path,
            required_columns=self.REQUIRED_COLUMNS,
        )

        self.repository = repository
        self.service = ClubImportService(
            repository
        )

    def run(
        self,
    ) -> tuple[int, int]:
        clubs = self.import_data()

        self.validate_clubs(
            clubs
        )

        return self.service.import_clubs(
            clubs
        )

    def validate_clubs(
        self,
        clubs: list[dict],
    ) -> None:
        club_ids: set[str] = set()

        for club in clubs:
            club_id = club["club_id"].strip()

            if not club_id:
                raise ValueError(
                    "Leere Vereins-ID gefunden."
                )

            if club_id in club_ids:
                raise ValueError(
                    f"Doppelte Vereins-ID: {club_id}"
                )

            club_ids.add(
                club_id
            )