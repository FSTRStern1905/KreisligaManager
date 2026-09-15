from __future__ import annotations

from src.importer.fussballde.browser import FussballDeBrowser


START_URL = "https://www.fussball.de/"


class CompetitionSelectorInspector:

    def __init__(
        self,
        browser: FussballDeBrowser,
    ) -> None:
        self.browser = browser

    def inspect(self) -> None:
        page = self.browser.page

        if page is None:
            raise RuntimeError(
                "Browser wurde noch nicht gestartet."
            )

        selects = page.locator("select")

        print("=" * 100)
        print("FUSSBALL.DE WETTBEWERBSAUSWAHL")
        print("=" * 100)
        print()

        print(
            f"Gefundene SELECT-Elemente: "
            f"{selects.count()}"
        )
        print()

        for index in range(selects.count()):
            select = selects.nth(index)

            try:
                data = select.evaluate(
                    """
                    element => ({
                        id: element.id || "",
                        name: element.name || "",
                        className:
                            element.className || "",
                        ariaLabel:
                            element.getAttribute(
                                "aria-label"
                            ) || "",
                        model:
                            element.getAttribute(
                                "ng-model"
                            ) || "",
                        change:
                            element.getAttribute(
                                "ng-change"
                            ) || "",
                        html:
                            element.outerHTML
                    })
                    """
                )

                options = select.locator("option")

                print("-" * 100)
                print(f"SELECT #{index}")
                print("-" * 100)

                print(
                    f"ID:        "
                    f"{data['id']}"
                )
                print(
                    f"Name:      "
                    f"{data['name']}"
                )
                print(
                    f"Klassen:   "
                    f"{data['className']}"
                )
                print(
                    f"ARIA:      "
                    f"{data['ariaLabel']}"
                )
                print(
                    f"ng-model:  "
                    f"{data['model']}"
                )
                print(
                    f"ng-change: "
                    f"{data['change']}"
                )

                print()
                print(
                    f"Optionen: {options.count()}"
                )

                for option_index in range(
                    min(
                        options.count(),
                        30,
                    )
                ):
                    option = options.nth(
                        option_index
                    )

                    option_data = (
                        option.evaluate(
                            """
                            element => ({
                                text:
                                    element.textContent
                                        .trim(),
                                value:
                                    element.value || "",
                                selected:
                                    element.selected,
                                disabled:
                                    element.disabled
                            })
                            """
                        )
                    )

                    marker = (
                        "*"
                        if option_data[
                            "selected"
                        ]
                        else " "
                    )

                    print(
                        f"{marker} "
                        f"[{option_index:02d}] "
                        f"{option_data['text']!r}"
                        f" -> "
                        f"{option_data['value']!r}"
                    )

                print()
                print("HTML:")
                print(
                    data["html"][:3000]
                )
                print()

            except Exception as error:
                print(
                    f"SELECT #{index} konnte "
                    f"nicht gelesen werden:"
                )
                print(error)
                print()

        self._inspect_buttons()

    def _inspect_buttons(self) -> None:
        page = self.browser.page

        if page is None:
            return

        print("=" * 100)
        print("RELEVANTE BUTTONS / LINKS")
        print("=" * 100)

        candidates = page.locator(
            "button, "
            "input[type='submit'], "
            "a"
        )

        found = 0

        for index in range(
            candidates.count()
        ):
            element = candidates.nth(index)

            try:
                text = (
                    element
                    .inner_text(
                        timeout=500
                    )
                    .strip()
                )

            except Exception:
                continue

            normalized = text.casefold()

            if not any(
                keyword in normalized
                for keyword in (
                    "anzeigen",
                    "favorit",
                    "ligen",
                )
            ):
                continue

            try:
                data = element.evaluate(
                    """
                    element => ({
                        tag:
                            element.tagName,
                        id:
                            element.id || "",
                        className:
                            element.className || "",
                        href:
                            element.href || "",
                        type:
                            element.type || ""
                    })
                    """
                )

                print()
                print(
                    f"{data['tag']} "
                    f"{text!r}"
                )
                print(
                    f"ID:      "
                    f"{data['id']}"
                )
                print(
                    f"Klassen: "
                    f"{data['className']}"
                )
                print(
                    f"Href:    "
                    f"{data['href']}"
                )
                print(
                    f"Type:    "
                    f"{data['type']}"
                )

                found += 1

            except Exception:
                continue

        print()
        print(
            f"Relevante Elemente: {found}"
        )


def main() -> None:
    browser = FussballDeBrowser()

    try:
        print(
            "Starte Chromium..."
        )

        browser.start(
            headless=False,
        )

        print(
            "Öffne FUSSBALL.DE..."
        )

        browser.open(
            START_URL,
            page_type=(
                FussballDeBrowser
                .PAGE_TYPE_GENERIC
            ),
        )

        inspector = (
            CompetitionSelectorInspector(
                browser
            )
        )

        inspector.inspect()

        print()
        print("=" * 100)
        print("INSPEKTION ABGESCHLOSSEN")
        print("=" * 100)

    finally:
        browser.close()


if __name__ == "__main__":
    main()