from typing import Iterable


class CSVValidator:
    def __init__(
        self,
        required_columns: Iterable[str],
    ):
        self.required_columns = set(required_columns)

    def validate_headers(
        self,
        headers: list[str],
    ) -> None:
        if not headers:
            raise ValueError(
                "Die CSV-Datei enthält keine Spalten."
            )

        duplicates = {
            column
            for column in headers
            if headers.count(column) > 1
        }

        if duplicates:
            duplicate_list = ", ".join(
                sorted(duplicates)
            )

            raise ValueError(
                f"Doppelte Spalten gefunden: {duplicate_list}"
            )

        missing = self.required_columns - set(headers)

        if missing:
            missing_list = ", ".join(
                sorted(missing)
            )

            raise ValueError(
                "Folgende Pflichtspalten fehlen: "
                f"{missing_list}"
            )

    def validate_rows(
        self,
        rows: list[dict],
    ) -> None:
        if not rows:
            raise ValueError(
                "Die CSV-Datei enthält keine Datensätze."
            )

        for index, row in enumerate(
            rows,
            start=2,
        ):
            if all(
                str(value).strip() == ""
                for value in row.values()
            ):
                raise ValueError(
                    f"Leere Zeile in CSV (Zeile {index})."
                )