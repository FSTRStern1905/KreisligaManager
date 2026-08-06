from __future__ import annotations

import traceback

from src.importer.fussballde.liveticker_explorer import (
    LivetickerExplorer,
)


MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "djk-tusa-06-duesseldorf-sgs-essen-u19/"
    "-/spiel/"
    "02Q4B8V3CS000000VS5489B4VTH92TNV"
)

HEADLESS = False


def main() -> None:
    print("=" * 70)
    print("LIVETICKER-EXPLORER TEST")
    print("=" * 70)
    print(f"URL: {MATCH_URL}")
    print("Browser wird gestartet ...")

    explorer = LivetickerExplorer()

    try:
        result = explorer.explore(
            url=MATCH_URL,
            headless=HEADLESS,
        )

        print()
        print("TEST ERFOLGREICH")
        print(
            f"Liveticker erkannt: "
            f"{'JA' if result.ticker_available else 'NEIN'}"
        )

    except Exception as error:
        print()
        print("TEST FEHLGESCHLAGEN")
        print(f"Fehler: {error}")
        print()
        traceback.print_exc()

    finally:
        print()
        input(
            "Zum Beenden ENTER drücken ..."
        )


if __name__ == "__main__":
    main()