from __future__ import annotations

import sys

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.complete_season_importer import (
    CompleteSeasonImporter,
)
from src.importer.fussballde.parsers.schedule_parser import (
    ScheduleParser,
)


DEFAULT_URL = (
    "https://www.fussball.de/spieltagsuebersicht/"
    "rheinlandliga-herren-rheinland-rheinlandliga-herren-"
    "saison2627-rheinland/-/staffel/"
    "031AU2ESDK00000IVS5489BUVV628VP4-G#!/"
)


def inspect_page(
    browser: FussballDeBrowser,
    label: str,
) -> None:
    if browser.page is None:
        raise RuntimeError(
            "Browser-Seite ist nicht verfügbar."
        )

    page = browser.page

    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    print(f"URL: {page.url}")

    for selector in (
        "#matchtable-date-from",
        "#matchtable-date-to",
    ):
        locator = page.locator(
            selector
        )

        if locator.count() < 1:
            print(
                f"{selector}: NICHT GEFUNDEN"
            )
            continue

        try:
            value = (
                locator.first.input_value()
                .strip()
            )
        except Exception as error:
            value = (
                f"FEHLER: {error}"
            )

        print(
            f"{selector}: {value}"
        )

    html = page.content()
    soup = BeautifulSoup(
        html,
        "lxml",
    )

    print()
    print("TABELLEN-CHECK")
    print("-" * 80)

    for selector in ScheduleParser.TABLE_SELECTORS:
        tables = soup.select(
            selector
        )

        print(
            f"{selector}: {len(tables)}"
        )

        for index, table in enumerate(
            tables,
            start=1,
        ):
            if not isinstance(
                table,
                Tag,
            ):
                continue

            rows = table.select(
                "tbody > tr"
            )

            headline_rows = [
                row
                for row in rows
                if isinstance(row, Tag)
                and "row-headline"
                in row.get(
                    "class",
                    [],
                )
            ]

            match_rows = [
                row
                for row in rows
                if isinstance(row, Tag)
                and len(
                    row.select(
                        "td.column-club"
                    )
                ) >= 2
            ]

            print(
                f"  Tabelle {index}: "
                f"Zeilen={len(rows)}, "
                f"Headlines={len(headline_rows)}, "
                f"Spielzeilen={len(match_rows)}"
            )

            if headline_rows:
                print(
                    "  Headlines:"
                )

                for headline in headline_rows[
                    :10
                ]:
                    text = " ".join(
                        headline.stripped_strings
                    )

                    print(
                        f"    {text}"
                    )

                if len(headline_rows) > 10:
                    print(
                        f"    ... +"
                        f"{len(headline_rows) - 10}"
                    )

    fixture_forms = soup.select(
        "form[data-ajax-resource*='ajax.fixturelist']"
    )

    print()
    print(
        "Fixture-Formulare:",
        len(fixture_forms),
    )

    for index, form in enumerate(
        fixture_forms,
        start=1,
    ):
        if not isinstance(
            form,
            Tag,
        ):
            continue

        print(
            f"  Formular {index}: "
            f"action={form.get('action')!r}, "
            f"data-ajax-resource="
            f"{form.get('data-ajax-resource')!r}"
        )


def inspect_parser(
    browser: FussballDeBrowser,
) -> None:
    if browser.page is None:
        raise RuntimeError(
            "Browser-Seite ist nicht verfügbar."
        )

    print()
    print("=" * 80)
    print("SCHEDULEPARSER-CHECK")
    print("=" * 80)

    parser = ScheduleParser(
        browser.page
    )
    data = parser.parse()

    matches = list(
        data.matches
    )

    print(
        f"Parser-Spiele: {len(matches)}"
    )

    matchdays = sorted(
        {
            match.matchday
            for match in matches
            if match.matchday is not None
        }
    )

    print(
        f"Erkannte Spieltage: {matchdays}"
    )

    without_matchday = [
        match
        for match in matches
        if match.matchday is None
    ]

    print(
        "Spiele ohne Spieltag:",
        len(without_matchday),
    )

    print()
    print("ERSTE 10 SPIELE")
    print("-" * 80)

    for match in matches[:10]:
        print_match(
            match
        )

    if len(matches) > 10:
        print()
        print("LETZTE 10 SPIELE")
        print("-" * 80)

        for match in matches[-10:]:
            print_match(
                match
            )


def print_match(
    match,
) -> None:
    print(
        f"ST={match.matchday!r} | "
        f"Nr={match.fixture_number!r} | "
        f"{match.date or '-'} "
        f"{match.time or '-'} | "
        f"{match.home_team} - "
        f"{match.away_team} | "
        f"{match.status}"
    )


def main() -> None:
    url = (
        sys.argv[1].strip()
        if len(sys.argv) > 1
        else DEFAULT_URL
    )

    browser = FussballDeBrowser()

    try:
        print(
            "Starte Chromium..."
        )

        browser.start(
            headless=False
        )

        print(
            "Öffne Staffel..."
        )

        browser.open(
            url
        )

        if browser.page is None:
            raise RuntimeError(
                "FUSSBALL.DE wurde nicht geladen."
            )

        inspect_page(
            browser,
            "VOR DATUMSFILTER",
        )

        print()
        print(
            "Wende CompleteSeasonImporter-"
            "Datumsfilter an..."
        )

        CompleteSeasonImporter._prepare_full_schedule_range(
            browser.page
        )

        inspect_page(
            browser,
            "NACH DATUMSFILTER",
        )

        inspect_parser(
            browser
        )

        print()
        print("=" * 80)
        print("DIAGNOSE ABGESCHLOSSEN")
        print("=" * 80)
        print(
            "Browser bleibt 5 Sekunden offen..."
        )

        browser.page.wait_for_timeout(
            5000
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()
