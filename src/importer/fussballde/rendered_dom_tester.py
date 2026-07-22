from __future__ import annotations

import sys

from src.importer.fussballde.browser import FussballDeBrowser


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.rendered_dom_tester "
            "\"https://www.fussball.de/spielplan/...\""
        )
        sys.exit(1)

    url = sys.argv[1]
    browser = FussballDeBrowser()

    try:
        browser.start()
        browser.open(url)

        if browser.page is None:
            raise RuntimeError(
                "Die fussball.de-Seite wurde nicht geladen."
            )

        page = browser.page

        rows = page.locator(
            "#fixtures-matchplan-table-matches-table tbody > tr"
        )

        row_count = rows.count()

        print(f"Gefundene Tabellenzeilen: {row_count}")
        print("=" * 80)

        shown_matches = 0

        for index in range(row_count):
            row = rows.nth(index)

            try:
                row_text = row.inner_text().strip()
            except Exception as exc:
                print(f"Zeile {index}: Fehler: {exc}")
                continue

            if not row_text:
                continue

            print()
            print(f"ZEILE {index}")
            print("-" * 80)
            print(row_text)

            club_cells = row.locator("td.column-club")

            if club_cells.count() >= 2:
                shown_matches += 1

            if shown_matches >= 10:
                break

    finally:
        browser.close()


if __name__ == "__main__":
    main()