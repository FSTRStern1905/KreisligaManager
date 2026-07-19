import csv
from pathlib import Path

from src.importer.base_importer import BaseImporter
from src.importer.validators import CSVValidator


class CSVImporter(BaseImporter):
    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8-sig",
        delimiter: str = ",",
        required_columns: list[str] | None = None,
    ):
        super().__init__(file_path)

        self.encoding = encoding
        self.delimiter = delimiter
        self.required_columns = required_columns or []

    def import_data(self) -> list[dict]:
        self.validate()

        headers = self.get_headers()

        validator = CSVValidator(
            self.required_columns
        )

        validator.validate_headers(headers)

        rows: list[dict] = []

        with open(
            self.file_path,
            mode="r",
            encoding=self.encoding,
            newline="",
        ) as csv_file:
            reader = csv.DictReader(
                csv_file,
                delimiter=self.delimiter,
            )

            for row in reader:
                rows.append(dict(row))

        validator.validate_rows(rows)

        return rows

    def get_headers(self) -> list[str]:
        self.validate()

        with open(
            self.file_path,
            mode="r",
            encoding=self.encoding,
            newline="",
        ) as csv_file:
            reader = csv.reader(
                csv_file,
                delimiter=self.delimiter,
            )

            return next(reader, [])

    def row_count(self) -> int:
        return len(self.import_data())