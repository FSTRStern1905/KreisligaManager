from __future__ import annotations

from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)

MATCH_ID = "02TNB07C34000000VS5489BUVSSD35NB"


def main() -> None:

    browser = FussballDeBrowser()

    try:

        browser.start(
            headless=False,
        )

        ajax_url = (
            "https://www.fussball.de/ajax.match.lineup/"
            f"-/mode/PAGE/spiel/{MATCH_ID}"
            "/ticker-id/selectedTickerId"
        )

        browser.open(
            ajax_url
        )

        if browser.page is None:
            raise RuntimeError(
                "AJAX-Seite konnte nicht geladen werden."
            )

        browser.page.wait_for_timeout(
            2000
        )

        html = browser.page.content()

        output_folder = Path(
            "data/temp"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            output_folder
            / "inspect_lineup_ajax.html"
        )

        output_file.write_text(
            html,
            encoding="utf-8",
        )

        print()
        print("=" * 60)
        print("AJAX-AUFSTELLUNG GESPEICHERT")
        print("=" * 60)
        print(output_file)

    finally:
        browser.close()


if __name__ == "__main__":
    main()