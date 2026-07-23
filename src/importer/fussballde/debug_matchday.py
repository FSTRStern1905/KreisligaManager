from __future__ import annotations

import re
import sys

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.font_decoder import FontDecoder


TABLE_SELECTOR = "#fixtures-matchplan-table-matches-table"

MATCHDAY_PATTERN = re.compile(
    r"\b(\d{1,2})\.\s*Spieltag\b",
    re.IGNORECASE,
)


def class_text(element: Tag) -> str:
    classes = element.get("class", [])

    if isinstance(classes, str):
        return classes

    if isinstance(classes, list):
        return " ".join(str(value) for value in classes)

    return ""


def decode_element_text(
    element: Tag,
    decoder: FontDecoder,
) -> str:
    parts: list[str] = []

    for text_node in element.find_all(string=True):
        text = str(text_node)

        if not text.strip():
            continue

        parent = text_node.parent
        decoded = text

        while isinstance(parent, Tag):
            font_id = decoder.extract_font_id(
                class_text(parent)
            )

            if font_id:
                try:
                    decoded = decoder.decode(
                        text=text,
                        font_id=font_id,
                    )
                except Exception:
                    decoded = text

                break

            if parent is element:
                break

            parent = parent.parent

        parts.append(decoded.strip())

    return " ".join(parts)


def print_attributes(
    element: Tag,
    prefix: str = "",
) -> None:
    for name, value in element.attrs.items():
        normalized_name = str(name).casefold()
        normalized_value = str(value).casefold()

        relevant_words = (
            "spieltag",
            "matchday",
            "match-day",
            "round",
            "day",
            "fixture",
        )

        if any(
            word in normalized_name
            or word in normalized_value
            for word in relevant_words
        ):
            print(
                f"{prefix}{element.name}: "
                f"{name}={value}"
            )


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.debug_matchday "
            "\"SPIELPLAN-URL\""
        )
        sys.exit(1)

    url = sys.argv[1]
    browser = FussballDeBrowser()

    try:
        print("Browser wird gestartet ...")
        browser.start()

        print("Spielplan wird geladen ...")
        browser.open(url)

        if browser.page is None:
            raise RuntimeError(
                "Die fussball.de-Seite wurde nicht geladen."
            )

        soup = BeautifulSoup(
            browser.page.content(),
            "lxml",
        )

        table = soup.select_one(TABLE_SELECTOR)

        if not isinstance(table, Tag):
            raise RuntimeError(
                "Die Spielplan-Tabelle wurde nicht gefunden."
            )

        decoder = FontDecoder(
            request_context=browser.page.request
        )

        print("\n" + "=" * 80)
        print("SUCHE NACH SPIELTAG-TEXTEN")
        print("=" * 80)

        found_texts: set[str] = set()

        for element in soup.find_all(True):
            if not isinstance(element, Tag):
                continue

            decoded_text = decode_element_text(
                element=element,
                decoder=decoder,
            )

            if not decoded_text:
                continue

            if "spieltag" not in decoded_text.casefold():
                continue

            cleaned = " ".join(decoded_text.split())

            if cleaned in found_texts:
                continue

            found_texts.add(cleaned)

            print(f"\nELEMENT: <{element.name}>")
            print(f"KLASSEN: {class_text(element)}")
            print(f"TEXT: {cleaned}")
            print(f"ATTRIBUTE: {dict(element.attrs)}")

        print("\n" + "=" * 80)
        print("SUCHE NACH RELEVANTEN ATTRIBUTEN")
        print("=" * 80)

        for element in soup.find_all(True):
            if isinstance(element, Tag):
                print_attributes(element)

        print("\n" + "=" * 80)
        print("ERSTE 10 SPIELZEILEN")
        print("=" * 80)

        match_rows = table.select(
            "tbody > tr:not(.row-headline)"
        )

        printed_rows = 0

        for index, row in enumerate(
            match_rows,
            start=1,
        ):
            if not isinstance(row, Tag):
                continue

            if not row.select_one("td.column-club"):
                continue

            decoded_text = decode_element_text(
                element=row,
                decoder=decoder,
            )

            matchday_match = MATCHDAY_PATTERN.search(
                decoded_text
            )

            print("\n" + "-" * 80)
            print(f"SPIELZEILE {index}")
            print("-" * 80)

            print("TEXT:")
            print(decoded_text)

            print("\nATTRIBUTE:")
            print(dict(row.attrs))

            print("\nELTERN-ELEMENTE:")

            parent = row.parent
            parent_level = 1

            while isinstance(parent, Tag):
                print(
                    f"{parent_level}. <{parent.name}> "
                    f"class=\"{class_text(parent)}\" "
                    f"attrs={dict(parent.attrs)}"
                )

                if parent is table:
                    break

                parent = parent.parent
                parent_level += 1

            print("\nGEFUNDENER SPIELTAG:")
            print(
                matchday_match.group(1)
                if matchday_match
                else "NICHT GEFUNDEN"
            )

            print("\nHTML:")
            print(row.prettify())

            printed_rows += 1

            if printed_rows >= 10:
                break

    finally:
        browser.close()


if __name__ == "__main__":
    main()