from __future__ import annotations

from pathlib import Path

from src.importer.fussballde.liveticker_type_id_explorer import (
    LivetickerTypeIdExplorer,
)


SOURCES = (
    Path(
        "02TKDR2LFG000000VS5489BUVUD1610F.zip"
    ),
    Path(
        "02TNB07DS8000000VS5489BUVSSD35NB.zip"
    ),
)

MAX_EXAMPLES_PER_TYPE = 5


def main() -> None:
    print("=" * 90)
    print("LIVETICKER TYPE-ID EXPLORER TEST")
    print("=" * 90)

    missing_sources = [
        source
        for source in SOURCES
        if not source.exists()
    ]

    if missing_sources:
        print()
        print("FEHLENDE DATEIEN")
        print("-" * 90)

        for source in missing_sources:
            print(source)

        print()
        print(
            "Lege beide ZIP-Dateien in den "
            "Projekt-Hauptordner:"
        )
        print(
            r"E:\Kreisligamanager"
        )
        return

    explorer = LivetickerTypeIdExplorer()

    explorer.explore(
        sources=SOURCES,
        max_examples_per_type=(
            MAX_EXAMPLES_PER_TYPE
        ),
    )


if __name__ == "__main__":
    main()