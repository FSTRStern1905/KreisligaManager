from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.browser import FussballDeBrowser


OUTPUT_FILE = Path(
    "data/temp/fussballde_match_detail.html"
)

KEYWORDS = (
    "aufstellung",
    "tore",
    "karten",
    "wechsel",
    "ereignisse",
    "spielbericht",
    "schiedsrichter",
    "zuschauer",
    "halbzeit",
)


def clean_text(value: str) -> str:
    return " ".join(value.split())


def print_page_overview(
    soup: BeautifulSoup,
) -> None:
    print("\n=== SEITENTITEL ===")

    title = soup.title

    if title is not None:
        print(clean_text(title.get_text(" ", strip=True)))
    else:
        print("Kein Seitentitel gefunden.")

    print("\n=== ÜBERSCHRIFTEN ===")

    for heading in soup.select(
        "h1, h2, h3, h4, h5"
    ):
        if not isinstance(heading, Tag):
            continue

        text = clean_text(
            heading.get_text(" ", strip=True)
        )

        if text:
            print(
                f"{heading.name}: {text}"
            )


def print_relevant_elements(
    soup: BeautifulSoup,
) -> None:
    print("\n=== RELEVANTE ELEMENTE ===")

    found_elements: set[str] = set()

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

        attributes = clean_text(
            f"{element_id} {class_text}"
        ).casefold()

        if not any(
            keyword in attributes
            for keyword in KEYWORDS
        ):
            continue

        selector_parts = [
            element.name,
        ]

        if element_id:
            selector_parts.append(
                f"#{element_id}"
            )

        if class_text:
            selector_parts.append(
                "."
                + ".".join(
                    class_text.split()
                )
            )

        selector = "".join(selector_parts)

        if selector in found_elements:
            continue

        found_elements.add(selector)

        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if len(text) > 250:
            text = text[:250] + " ..."

        print(f"\n{selector}")
        print(text or "(kein Text)")


def print_match_links(
    soup: BeautifulSoup,
) -> None:
    print("\n=== LINKS UND TABS ===")

    for link in soup.select("a[href]"):
        if not isinstance(link, Tag):
            continue

        text = clean_text(
            link.get_text(" ", strip=True)
        )

        href = clean_text(
            str(link.get("href", ""))
        )

        combined = (
            f"{text} {href}"
        ).casefold()

        if not any(
            keyword in combined
            for keyword in KEYWORDS
        ):
            continue

        print(
            f"{text or '(ohne Text)'} -> {href}"
        )


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m "
            "src.importer.fussballde."
            "match_detail_inspector "
            "\"SPIEL-URL\""
        )
        sys.exit(1)

    url = sys.argv[1]

    browser = FussballDeBrowser()

    try:
        print("Browser wird gestartet ...")
        browser.start(
            headless=False,
        )

        print("Spieldetailseite wird geladen ...")
        browser.open(url)

        if browser.page is None:
            raise RuntimeError(
                "Die Spieldetailseite wurde "
                "nicht geladen."
            )

        browser.page.wait_for_timeout(
            3_000
        )

        html = browser.page.content()

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_FILE.write_text(
            html,
            encoding="utf-8",
        )

        soup = BeautifulSoup(
            html,
            "lxml",
        )

        print_page_overview(soup)
        print_relevant_elements(soup)
        print_match_links(soup)

        print(
            "\nHTML gespeichert unter:\n"
            f"{OUTPUT_FILE.resolve()}"
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()