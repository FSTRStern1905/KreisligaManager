from __future__ import annotations

from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "sv-trier-irsch-sv-foehren/-/spiel/"
    "02TNB07C34000000VS5489BUVSSD35NB"
)


def main() -> None:

    browser = FussballDeBrowser()

    try:

        browser.start(
            headless=False,
        )

        browser.open(
            MATCH_URL
        )

        if browser.page is None:
            raise RuntimeError(
                "Seite konnte nicht geladen werden."
            )

        browser.page.wait_for_timeout(
            3000
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
            / "inspect_lineups.html"
        )

        output_file.write_text(
            html,
            encoding="utf-8",
        )

        print()
        print("=" * 60)
        print("AUFSTELLUNGSSEITE GESPEICHERT")
        print("=" * 60)
        print(output_file)

    finally:
        browser.close()


if __name__ == "__main__":
    main()