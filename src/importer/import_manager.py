from pathlib import Path

from src.importer.base_importer import (
    BaseImporter,
)
from src.importer.csv_importer import (
    CSVImporter,
)


class ImportManager:
    SUPPORTED_FILE_EXTENSIONS = {
        ".csv",
    }

    def validate_file(
        self,
        file_path: str | Path,
    ) -> Path:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Die Importdatei wurde nicht gefunden: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Der angegebene Pfad ist keine Datei: {path}"
            )

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_FILE_EXTENSIONS:
            supported_extensions = ", ".join(
                sorted(
                    self.SUPPORTED_FILE_EXTENSIONS
                )
            )

            raise ValueError(
                "Nicht unterstütztes Dateiformat. "
                f"Erlaubt sind: {supported_extensions}"
            )

        return path

    def create_importer(
        self,
        file_path: str | Path,
    ) -> BaseImporter:
        path = self.validate_file(
            file_path
        )

        extension = path.suffix.lower()

        if extension == ".csv":
            return CSVImporter(
                path
            )

        raise ValueError(
            f"Kein Importer für {extension} vorhanden."
        )

    def import_file(
        self,
        file_path: str | Path,
    ) -> list[dict]:
        importer = self.create_importer(
            file_path
        )

        return importer.import_data()

    def get_file_type(
        self,
        file_path: str | Path,
    ) -> str:
        path = self.validate_file(
            file_path
        )

        extension = path.suffix.lower()

        if extension == ".csv":
            return "csv"

        raise ValueError(
            f"Unbekannter Dateityp: {extension}"
        )