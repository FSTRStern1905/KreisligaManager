from __future__ import annotations

import sys

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.parsers.schedule_parser import ScheduleParser


DEFAULT_URL = (
    "https://www.fussball.de/spielplan/"
    "rheinlandliga-herren-rheinland-rheinlandliga-herren-"
    "saison2627-rheinland/-/staffel/"
    "031AU2ESDK00000IVS5489BUVV628VP4-G#!/section/matchplan"
)

DATE_FROM = "01.07.2026"
DATE_TO = "30.06.2027"


def inspect_date_fields(page) -> None:
    print()
    print("=" * 80)
    print("DATUMSFELDER")
    print("=" * 80)

    inputs = page.locator("input")
    print(f"Inputs gesamt: {inputs.count()}")

    for index in range(inputs.count()):
        element = inputs.nth(index)

        try:
            element_id = element.get_attribute("id") or ""
            name = element.get_attribute("name") or ""
            value = element.input_value()
            placeholder = element.get_attribute("placeholder") or ""
            input_type = element.get_attribute("type") or ""

            haystack = " ".join(
                (
                    element_id,
                    name,
                    placeholder,
                    value,
                )
            ).lower()

            if (
                "date" in haystack
                or "datum" in haystack
                or "von" in haystack
                or "bis" in haystack
                or "matchplan" in haystack
                or "fixture" in haystack
                or input_type == "date"
                or value.count(".") == 2
            ):
                print(
                    f"[{index}] "
                    f"id={element_id!r} | "
                    f"name={name!r} | "
                    f"type={input_type!r} | "
                    f"value={value!r} | "
                    f"placeholder={placeholder!r}"
                )
        except Exception:
            pass


def count_matches(page, label: str) -> None:
    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    parser = ScheduleParser(page)
    data = parser.parse()
    matches = data.matches

    matchdays = sorted(
        {
            match.matchday
            for match in matches
            if match.matchday is not None
        }
    )

    fixture_numbers = sorted(
        match.fixture_number
        for match in matches
        if match.fixture_number is not None
    )

    print()
    print(f"Parser-Spiele: {len(matches)}")
    print(f"Spieltage: {matchdays}")
    print(
        "Spiele ohne Spieltag: "
        f"{sum(m.matchday is None for m in matches)}"
    )

    if fixture_numbers:
        print(
            f"Spielnummern: "
            f"{fixture_numbers[0]} bis "
            f"{fixture_numbers[-1]}"
        )


def set_date_input(page, selector: str, value: str) -> None:
    result = page.locator(selector).evaluate(
        """
        (element, value) => {
            element.value = value;

            element.dispatchEvent(
                new Event("input", {
                    bubbles: true
                })
            );

            element.dispatchEvent(
                new Event("change", {
                    bubbles: true
                })
            );

            if (
                window.angular &&
                window.angular.element
            ) {
                try {
                    const ngElement =
                        window.angular.element(element);

                    const model =
                        ngElement.controller("ngModel");

                    if (model) {
                        model.$setViewValue(value);
                        model.$render();
                    }
                } catch (error) {
                    console.log(
                        "Angular update failed",
                        error
                    );
                }
            }

            return element.value;
        }
        """,
        value,
    )

    print(
        f"{selector} -> {result}"
    )


def find_date_inputs(page):
    date_from = page.locator(
        "#matchtable-date-from"
    )
    date_to = page.locator(
        "#matchtable-date-to"
    )

    if (
        date_from.count() == 0
        or date_to.count() == 0
    ):
        raise RuntimeError(
            "Staffelspielplan-Datumsfelder "
            "nicht gefunden."
        )

    return date_from, date_to


def submit_matchplan(page) -> None:
    print()
    print("Suche passenden Aktualisieren-/Anzeigen-Button...")

    selectors = (
        "form:has(#matchplan-date-from) button[type='submit']",
        "form:has(input[value*='.']) button[type='submit']",
        "button[type='submit']",
        "input[type='submit']",
    )

    for selector in selectors:
        buttons = page.locator(selector)

        for index in range(buttons.count()):
            button = buttons.nth(index)

            try:
                if not button.is_visible():
                    continue

                text = (
                    button.inner_text()
                    if button.evaluate(
                        "(e) => e.tagName.toLowerCase() === 'button'"
                    )
                    else button.get_attribute("value") or ""
                ).strip()

                print(
                    f"  Kandidat: {text!r} "
                    f"({selector})"
                )

                lowered = text.lower()

                if (
                    "anzeigen" in lowered
                    or "suchen" in lowered
                    or "aktual" in lowered
                    or "filtern" in lowered
                ):
                    print(
                        f"Klicke Button: {text!r}"
                    )

                    button.click()
                    page.wait_for_timeout(3000)
                    return
            except Exception:
                pass

    print(
        "Kein eindeutiger Button gefunden. "
        "Versuche Enter im Bis-Feld."
    )

    _, date_to = find_date_inputs(page)
    date_to.press("Enter")
    page.wait_for_timeout(3000)


def main() -> None:
    url = (
        sys.argv[1].strip()
        if len(sys.argv) > 1
        else DEFAULT_URL
    )

    browser = FussballDeBrowser()

    try:
        print("Starte Chromium...")
        browser.start(headless=False)

        if browser.page is None:
            raise RuntimeError(
                "Browser-Seite wurde nicht erstellt."
            )

        page = browser.page

        print("Öffne Staffelspielplan...")
        browser.open(url)
        page.wait_for_timeout(3000)

        inspect_date_fields(page)
        count_matches(
            page,
            "VOR DATUMSÄNDERUNG",
        )

        date_from, date_to = find_date_inputs(
            page
        )

        print()
        print("=" * 80)
        print("SETZE SAISONZEITRAUM")
        print("=" * 80)

        print(
            f"Von vorher: {date_from.input_value()}"
        )
        print(
            f"Bis vorher: {date_to.input_value()}"
        )

        set_date_input(
            page,
            "#matchtable-date-from",
            DATE_FROM,
        )
        set_date_input(
            page,
            "#matchtable-date-to",
            DATE_TO,
        )

        print(
            f"Von gesetzt: {date_from.input_value()}"
        )
        print(
            f"Bis gesetzt: {date_to.input_value()}"
        )

        submit_matchplan(page)

        print()
        print(f"Aktuelle URL: {page.url}")

        inspect_date_fields(page)

        count_matches(
            page,
            "NACH DATUMSÄNDERUNG",
        )

        print()
        print("=" * 80)
        print("ZIEL")
        print("=" * 80)
        print(
            "Erwartung bei 18 Mannschaften: "
            "306 Spiele / Spieltage 1-34"
        )

        page.wait_for_timeout(5000)

    finally:
        browser.close()


if __name__ == "__main__":
    main()
