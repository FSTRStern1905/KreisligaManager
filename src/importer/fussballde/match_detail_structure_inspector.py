from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag


DEFAULT_HTML_FILE = Path(
    "data/temp/fussballde_match_detail.html"
)

SEARCH_TERMS = (
    "TuS Schillingen",
    "FSG Ehrang-Pfalzel",
    "Anpfiff",
    "Abpfiff",
    "Halbzeit",
    "Tor",
    "Gelbe Karte",
    "Rote Karte",
    "Auswechslung",
)


def clean_text(value: str) -> str:
    return " ".join(value.split())


def element_selector(element: Tag) -> str:
    selector = element.name

    element_id = element.get("id")

    if element_id:
        selector += f"#{element_id}"

    classes = element.get("class", [])

    if isinstance(classes, list) and classes:
        selector += "." + ".".join(
            str(value)
            for value in classes
        )

    return selector


def print_element_details(
    element: Tag,
    term: str,
) -> None:
    print("\n" + "=" * 100)
    print(f"SUCHBEGRIFF: {term}")
    print("=" * 100)

    current: Tag | None = element

    for level in range(5):
        if current is None:
            break

        text = clean_text(
            current.get_text(
                " ",
                strip=True,
            )
        )

        if len(text) > 1_500:
            text = text[:1_500] + " ..."

        print(f"\nEBENE {level}")
        print(f"SELECTOR: {element_selector(current)}")
        print(f"ATTRIBUTE: {dict(current.attrs)}")
        print(f"TEXT:\n{text}")

        parent = current.parent

        if isinstance(parent, Tag):
            current = parent
        else:
            current = None


def inspect_search_terms(
    soup: BeautifulSoup,
) -> None:
    page_text = soup.get_text(
        " ",
        strip=True,
    )

    for term in SEARCH_TERMS:
        if term.casefold() not in page_text.casefold():
            print(
                f"\nNicht gefunden: {term}"
            )
            continue

        matches = soup.find_all(
            string=lambda value: (
                value is not None
                and term.casefold()
                in str(value).casefold()
            )
        )

        print(
            f"\nGefunden: {term} "
            f"({len(matches)} Treffer)"
        )

        for match in matches[:3]:
            parent = match.parent

            if isinstance(parent, Tag):
                print_element_details(
                    element=parent,
                    term=term,
                )


def inspect_match_related_classes(
    soup: BeautifulSoup,
) -> None:
    print("\n" + "=" * 100)
    print("MATCH- UND TIMELINE-KLASSEN")
    print("=" * 100)

    keywords = (
        "match",
        "game",
        "fixture",
        "event",
        "timeline",
        "ticker",
        "result",
        "score",
        "club",
        "team",
    )

    found_selectors: set[str] = set()

    for element in soup.find_all(True):
        if not isinstance(element, Tag):
            continue

        element_id = str(
            element.get("id", "")
        )

        classes = element.get("class", [])

        if isinstance(classes, list):
            class_text = " ".join(
                str(value)
                for value in classes
            )
        else:
            class_text = str(classes)

        searchable = (
            f"{element_id} {class_text}"
        ).casefold()

        if not any(
            keyword in searchable
            for keyword in keywords
        ):
            continue

        selector = element_selector(element)

        if selector in found_selectors:
            continue

        found_selectors.add(selector)

        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if len(text) > 500:
            text = text[:500] + " ..."

        print(f"\n{selector}")
        print(dict(element.attrs))
        print(text or "(kein Text)")


def inspect_scripts(
    soup: BeautifulSoup,
) -> None:
    print("\n" + "=" * 100)
    print("RELEVANTE SCRIPT-INHALTE")
    print("=" * 100)

    keywords = (
        "02TNB07LFO000000VS5489BUVSSD35NB",
        "TuS Schillingen",
        "FSG Ehrang-Pfalzel",
        "Anpfiff",
        "Abpfiff",
    )

    for index, script in enumerate(
        soup.find_all("script"),
        start=1,
    ):
        script_text = script.string or script.get_text()

        if not script_text:
            continue

        if not any(
            keyword.casefold()
            in script_text.casefold()
            for keyword in keywords
        ):
            continue

        cleaned_script = clean_text(script_text)

        if len(cleaned_script) > 3_000:
            cleaned_script = (
                cleaned_script[:3_000]
                + " ..."
            )

        print(f"\nSCRIPT {index}")
        print(cleaned_script)


def main() -> None:
    html_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else DEFAULT_HTML_FILE
    )

    if not html_file.exists():
        raise FileNotFoundError(
            f"HTML-Datei nicht gefunden: "
            f"{html_file.resolve()}"
        )

    html = html_file.read_text(
        encoding="utf-8",
    )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    print(
        f"Analysiere:\n{html_file.resolve()}"
    )

    inspect_search_terms(soup)
    inspect_match_related_classes(soup)
    inspect_scripts(soup)


if __name__ == "__main__":
    main()