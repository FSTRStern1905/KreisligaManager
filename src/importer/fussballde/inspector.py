import sys
from typing import Any

from playwright.sync_api import Locator

from src.importer.fussballde.browser import FussballDeBrowser


class FussballDeInspector:
    """
    Untersucht eine geladene fussball.de-Seite und gibt relevante
    Seitenelemente für die spätere Parser-Entwicklung aus.
    """

    def __init__(self, browser: FussballDeBrowser):
        self.browser = browser

    def inspect(self) -> None:
        page = getattr(self.browser, "page", None)

        if page is None:
            raise RuntimeError(
                "Der Browser wurde noch nicht gestartet "
                "oder es wurde noch keine Seite geöffnet."
            )

        print("\n" + "=" * 80)
        print("FUSSBALL.DE INSPECTOR")
        print("=" * 80)

        print(f"Titel: {page.title()}")
        print(f"URL:   {page.url}")

        self._print_headings(page.locator("h1, h2, h3, h4, h5, h6"))
        self._print_buttons(
            page.locator(
                "button, "
                "input[type='button'], "
                "input[type='submit'], "
                "[role='button']"
            )
        )
        self._print_links(page.locator("a[href]"))
        self._print_tables(page.locator("table"))

        print("\n" + "=" * 80)
        print("INSPEKTION ABGESCHLOSSEN")
        print("=" * 80)

    def _print_headings(self, locator: Locator) -> None:
        print("\n" + "-" * 80)
        print("ÜBERSCHRIFTEN")
        print("-" * 80)

        elements = self._visible_elements(locator)

        if not elements:
            print("Keine sichtbaren Überschriften gefunden.")
            return

        for index, element in enumerate(elements, start=1):
            tag_name = self._tag_name(element)
            text = self._clean_text(self._safe_inner_text(element))

            if not text:
                continue

            print(f"[{index:03}] <{tag_name}> {text}")

    def _print_buttons(self, locator: Locator) -> None:
        print("\n" + "-" * 80)
        print("BUTTONS")
        print("-" * 80)

        elements = self._visible_elements(locator)

        if not elements:
            print("Keine sichtbaren Buttons gefunden.")
            return

        output_index = 1

        for element in elements:
            text = self._clean_text(self._safe_inner_text(element))
            aria_label = self._safe_attribute(element, "aria-label")
            title = self._safe_attribute(element, "title")
            element_id = self._safe_attribute(element, "id")
            css_class = self._safe_attribute(element, "class")

            label = text or aria_label or title or "(ohne Beschriftung)"

            print(f"[{output_index:03}] {label}")
            print(f"      Tag:      {self._tag_name(element)}")

            if element_id:
                print(f"      ID:       {element_id}")

            if css_class:
                print(f"      Klasse:   {self._shorten(css_class, 160)}")

            if aria_label:
                print(f"      Aria:     {aria_label}")

            output_index += 1

    def _print_links(self, locator: Locator) -> None:
        print("\n" + "-" * 80)
        print("LINKS")
        print("-" * 80)

        elements = self._visible_elements(locator)

        if not elements:
            print("Keine sichtbaren Links gefunden.")
            return

        output_index = 1
        seen_links: set[tuple[str, str]] = set()

        for element in elements:
            text = self._clean_text(self._safe_inner_text(element))
            href = self._safe_attribute(element, "href")

            if not href:
                continue

            link_key = (text, href)

            if link_key in seen_links:
                continue

            seen_links.add(link_key)

            label = text or "(Link ohne Text)"

            print(f"[{output_index:03}] {self._shorten(label, 140)}")
            print(f"      URL: {self._shorten(href, 220)}")

            output_index += 1

    def _print_tables(self, locator: Locator) -> None:
        print("\n" + "-" * 80)
        print("TABELLEN")
        print("-" * 80)

        tables = self._visible_elements(locator)

        if not tables:
            print("Keine sichtbaren HTML-Tabellen gefunden.")
            return

        for table_index, table in enumerate(tables, start=1):
            print(f"\nTabelle {table_index}")
            print("." * 80)

            table_id = self._safe_attribute(table, "id")
            table_class = self._safe_attribute(table, "class")

            if table_id:
                print(f"ID:     {table_id}")

            if table_class:
                print(f"Klasse: {self._shorten(table_class, 180)}")

            rows = table.locator("tr")
            row_count = rows.count()

            if row_count == 0:
                print("Keine Tabellenzeilen gefunden.")
                continue

            maximum_rows = min(row_count, 25)

            for row_index in range(maximum_rows):
                row = rows.nth(row_index)
                cells = row.locator("th, td")

                cell_values: list[str] = []

                for cell_index in range(cells.count()):
                    cell = cells.nth(cell_index)
                    text = self._clean_text(self._safe_inner_text(cell))

                    if text:
                        cell_values.append(self._shorten(text, 100))
                    else:
                        cell_values.append("")

                if cell_values:
                    print(
                        f"[{row_index + 1:02}] "
                        + " | ".join(cell_values)
                    )

            if row_count > maximum_rows:
                remaining_rows = row_count - maximum_rows
                print(f"... weitere {remaining_rows} Zeilen ausgeblendet")

    @staticmethod
    def _visible_elements(locator: Locator) -> list[Locator]:
        elements: list[Locator] = []

        for index in range(locator.count()):
            element = locator.nth(index)

            try:
                if element.is_visible():
                    elements.append(element)
            except Exception:
                continue

        return elements

    @staticmethod
    def _safe_inner_text(element: Locator) -> str:
        try:
            return element.inner_text(timeout=1_000)
        except Exception:
            return ""

    @staticmethod
    def _safe_attribute(element: Locator, name: str) -> str:
        try:
            value = element.get_attribute(name, timeout=1_000)
            return value or ""
        except Exception:
            return ""

    @staticmethod
    def _tag_name(element: Locator) -> str:
        try:
            return element.evaluate(
                "(element) => element.tagName.toLowerCase()"
            )
        except Exception:
            return "unbekannt"

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""

        return " ".join(str(value).split())

    @staticmethod
    def _shorten(value: str, maximum_length: int) -> str:
        if len(value) <= maximum_length:
            return value

        return value[: maximum_length - 3] + "..."


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.inspector "
            "\"https://www.fussball.de/...\""
        )
        sys.exit(1)

    url = sys.argv[1]

    browser = FussballDeBrowser()

    try:
        browser.start()
        browser.open(url)

        inspector = FussballDeInspector(browser)
        inspector.inspect()
    finally:
        browser.close()


if __name__ == "__main__":
    main()