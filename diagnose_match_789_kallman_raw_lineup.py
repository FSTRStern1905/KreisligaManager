from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup


EXTERNAL_MATCH_ID = (
    "031BG6B7PG000000VS5489BUVUR5FS5A"
)

PLAYER_EXTERNAL_ID = (
    "02TUJFD0M4000000VUM1D52BVUTAQN0Q"
)

HTML_PATH = Path(
    "debug/lineup"
) / f"{EXTERNAL_MATCH_ID}.html"


def clean_text(value: str) -> str:
    return " ".join(
        (value or "").split()
    )


def main() -> None:
    if not HTML_PATH.exists():
        raise FileNotFoundError(
            f"Lineup-HTML fehlt: {HTML_PATH}"
        )

    html = HTML_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    print("=" * 110)
    print("DIAGNOSE KÄLLMAN - LINEUP ROHDATEN")
    print("=" * 110)
    print(f"Datei: {HTML_PATH}")
    print(f"HTML-Länge: {len(html)}")
    print()

    print("TEXTTREFFER")
    print("-" * 110)

    for needle in (
        "Källman",
        "Kallman",
        "Paul Benjamin",
        "Sven-Eber",
        PLAYER_EXTERNAL_ID,
    ):
        print(
            f"{needle:<45} "
            f"→ {html.casefold().count(needle.casefold())}"
        )

    print()

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    matching_elements = []

    for element in soup.find_all(
        href=True
    ):
        href = str(
            element.get("href", "")
        )

        if PLAYER_EXTERNAL_ID in href:
            matching_elements.append(
                element
            )

    for element in soup.find_all(
        attrs={
            "data-player-id": True
        }
    ):
        if (
            str(
                element.get(
                    "data-player-id",
                    "",
                )
            )
            == PLAYER_EXTERNAL_ID
        ):
            matching_elements.append(
                element
            )

    unique_elements = []
    seen_ids = set()

    for element in matching_elements:
        marker = id(element)

        if marker in seen_ids:
            continue

        seen_ids.add(marker)
        unique_elements.append(
            element
        )

    print("ELEMENTE MIT SPIELER-ID")
    print("-" * 110)

    if not unique_elements:
        print(
            "Kein Element über die Spieler-ID gefunden."
        )

    for index, element in enumerate(
        unique_elements,
        start=1,
    ):
        print(
            f"\n[{index}] TAG: {element.name}"
        )
        print(
            f"Text: {clean_text(element.get_text(' ', strip=True))!r}"
        )
        print(
            f"Attribute: {dict(element.attrs)}"
        )

        parent = element

        for level in range(1, 6):
            parent = parent.parent

            if parent is None:
                break

            parent_text = clean_text(
                parent.get_text(
                    " ",
                    strip=True,
                )
            )

            print(
                f"\n  PARENT {level}: "
                f"<{parent.name}>"
            )
            print(
                f"  Text: {parent_text!r}"
            )

            if (
                "Källman".casefold()
                in parent_text.casefold()
                or "Paul Benjamin".casefold()
                in parent_text.casefold()
            ):
                print(
                    "  >>> RELEVANTER CONTAINER"
                )

    print()
    print("=" * 110)
    print("HTML-AUSSCHNITTE UM TREFFER")
    print("=" * 110)

    patterns = (
        PLAYER_EXTERNAL_ID,
        "Källman",
        "Paul Benjamin",
    )

    printed_ranges = set()

    for pattern in patterns:
        for match in re.finditer(
            re.escape(pattern),
            html,
            flags=re.IGNORECASE,
        ):
            start = max(
                0,
                match.start() - 600,
            )
            end = min(
                len(html),
                match.end() + 600,
            )

            range_key = (
                start // 300,
                end // 300,
            )

            if range_key in printed_ranges:
                continue

            printed_ranges.add(
                range_key
            )

            print(
                f"\n--- Treffer: {pattern} ---"
            )
            print(
                html[start:end]
            )

    print()
    print("=" * 110)

    if "Källman".casefold() in html.casefold():
        print(
            "ERGEBNIS: 'Källman' ist im Roh-HTML vorhanden. "
            "Der Fehler liegt im LineupParser."
        )
    else:
        print(
            "ERGEBNIS: 'Källman' fehlt bereits im Roh-HTML. "
            "Dann brauchen wir eine alternative Datenquelle/"
            "Matching-Regel."
        )

    print("=" * 110)


if __name__ == "__main__":
    main()
