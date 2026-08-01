from __future__ import annotations

from pathlib import Path

from src.database.database import Database
from src.database.schema import DatabaseSchema
from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.lineup_importer import (
    LineupImporter,
)


MATCH_EXTERNAL_ID = (
    "02TNB07C34000000VS5489BUVSSD35NB"
)

LINEUP_HTML_PATH = Path(
    "data/temp/inspect_lineup_ajax.html"
)


def main() -> None:
    if not LINEUP_HTML_PATH.exists():
        raise FileNotFoundError(
            "Die gespeicherte AJAX-Aufstellung "
            "wurde nicht gefunden:\n"
            f"{LINEUP_HTML_PATH}"
        )

    database = Database(
        database_name="kreisligamanager_test.db",
    )

    connection = database.connect()

    try:
        DatabaseSchema(
            connection
        ).create_all_tables()

        html = LINEUP_HTML_PATH.read_text(
            encoding="utf-8"
        )

        browser = FussballDeBrowser()

        try:
            browser.start(
                headless=True,
            )

            if browser.page is None:
                raise RuntimeError(
                    "Browserseite wurde nicht erstellt."
                )

            importer = LineupImporter(
                connection=connection,
            )

            result = importer.import_from_html(
                html=html,
                match_external_id=(
                    MATCH_EXTERNAL_ID
                ),
                request_context=(
                    browser.page.request
                ),
            )

        finally:
            browser.close()

        print()
        print("=" * 60)
        print("LINEUP IMPORT ABGESCHLOSSEN")
        print("=" * 60)

        for key, value in result.items():
            print(f"{key}: {value}")

    finally:
        database.close()


if __name__ == "__main__":
    main()