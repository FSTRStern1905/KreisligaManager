from __future__ import annotations

from src.importer.fussballde.liveticker_explorer import (
    LivetickerExplorer,
)


MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "djk-tusa-06-duesseldorf-sgs-essen-u19/"
    "-/spiel/"
    "02Q4B8V3CS000000VS5489B4VTH92TNV"
)

HEADLESS = True


def main() -> None:
    explorer = LivetickerExplorer()

    explorer.explore(
        url=MATCH_URL,
        headless=HEADLESS,
    )


if __name__ == "__main__":
    main()