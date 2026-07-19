from abc import ABC, abstractmethod
from pathlib import Path


class BaseImporter(ABC):
    def __init__(
        self,
        file_path: str | Path,
    ):
        self.file_path = Path(file_path)

    @property
    def file_exists(self) -> bool:
        return self.file_path.exists()

    @property
    def file_name(self) -> str:
        return self.file_path.name

    @property
    def file_extension(self) -> str:
        return self.file_path.suffix.lower()

    def validate(self) -> None:
        if not self.file_exists:
            raise FileNotFoundError(
                f"Datei nicht gefunden:\n{self.file_path}"
            )

        if not self.file_path.is_file():
            raise ValueError(
                f"Ungültige Datei:\n{self.file_path}"
            )

    @abstractmethod
    def import_data(self):
        """
        Importiert die Daten und gibt
        das Ergebnis zurück.
        """
        raise NotImplementedError