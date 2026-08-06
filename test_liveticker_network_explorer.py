from __future__ import annotations

import traceback

from src.importer.fussballde.liveticker_network_explorer import (
    LivetickerNetworkExplorer,
)


LIVETICKER_URL = (
    "https://www.fussball.de/spiel/"
    "sv-trier-irsch-sg-niederkell-waldweiler/"
    "-/spiel/"
    "02TNB07DS8000000VS5489BUVSSD35NB/"
    "tab/liveTicker/"
)

HEADLESS = False


def main() -> None:
    print("=" * 78)
    print("LIVETICKER NETWORK TEST")
    print("=" * 78)
    print(f"URL: {LIVETICKER_URL}")

    explorer = LivetickerNetworkExplorer()

    try:
        explorer.explore(
            url=LIVETICKER_URL,
            headless=HEADLESS,
        )

        print()
        print("NETZWERKTEST ERFOLGREICH")

    except Exception as error:
        print()
        print("NETZWERKTEST FEHLGESCHLAGEN")
        print(f"Fehler: {error}")
        print()
        traceback.print_exc()

    finally:
        print()
        input("Zum Beenden ENTER drücken ...")


if __name__ == "__main__":
    main()