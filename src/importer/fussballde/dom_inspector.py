from __future__ import annotations

import re
import sys

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.browser import FussballDeBrowser


DATE_PATTERN = re.compile(r"\d{1,2}\.\d{1,2}\.(?:\d{2}|\d{4})")
TIME_PATTERN = re.compile(r"\b([01]?\d|2[0-3]):[0-5]\d\b")
SCORE_PATTERN = re.compile(r"\b\d{1,2}\s*:\s*\d{1,2}\b")


class DomInspector:

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "lxml")

    def inspect(self, match_index: int = 0) -> None:

        links = self.soup.select('a[href*="/spiel/"]')

        print("=" * 100)
        print(f"Gefundene Spiel-Links: {len(links)}")
        print("=" * 100)

        if not links:
            return

        if match_index >= len(links):
            print("Ungültiger Matchindex.")
            return

        link = links[match_index]

        print()
        print("=" * 100)
        print("UNTERSUCHTER SPIELLINK")
        print("=" * 100)
        print(link.get("href"))
        print()

        current = link

        for level in range(10):

            if not isinstance(current, Tag):
                break

            print("=" * 100)
            print(f"PARENT {level}")
            print("=" * 100)

            self.print_node(current)

            current = current.parent

    def print_node(self, node: Tag):

        tag = node.name

        node_id = node.get("id", "")

        classes = " ".join(node.get("class", []))

        text = " ".join(node.get_text(" ", strip=True).split())

        html = str(node)

        print(f"Tag:       {tag}")
        print(f"ID:        {node_id}")
        print(f"Klassen:   {classes}")
        print(f"Textlänge: {len(text)}")

        print()
        print("Analysen")
        print("-" * 80)

        print(
            "Spiellinks: ",
            len(node.select('a[href*="/spiel/"]'))
        )

        print(
            "Teamlinks: ",
            len(
                node.select(
                    'a[href*="/mannschaft/"],'
                    'a[href*="/verein/"],'
                    'a[href*="/team/"]'
                )
            )
        )

        print(
            "Datumsfelder:",
            len(DATE_PATTERN.findall(text))
        )

        print(
            "Uhrzeiten:",
            len(TIME_PATTERN.findall(text))
        )

        print(
            "Ergebnisse:",
            len(SCORE_PATTERN.findall(text))
        )

        print()

        print("TEXT")
        print("-" * 80)
        print(text[:800])

        print()

        print("HTML")
        print("-" * 80)
        print(html[:2500])

        print()


def main():

    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.dom_inspector URL [Index]"
        )
        return

    url = sys.argv[1]

    index = 0

    if len(sys.argv) >= 3:
        index = int(sys.argv[2])

    browser = FussballDeBrowser()

    try:

        browser.start()

        browser.open(url)

        inspector = DomInspector(browser.html())

        inspector.inspect(index)

    finally:

        browser.close()


if __name__ == "__main__":
    main()