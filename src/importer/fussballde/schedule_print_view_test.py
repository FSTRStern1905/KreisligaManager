from __future__ import annotations

import re
import sys
from urllib.parse import urljoin

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.parsers.schedule_parser import ScheduleParser


DEFAULT_URL = (
    "https://www.fussball.de/spieltagsuebersicht/"
    "rheinlandliga-herren-rheinland-rheinlandliga-herren-"
    "saison2627-rheinland/-/staffel/"
    "031AU2ESDK00000IVS5489BUVV628VP4-G#!/"
)


def count_schedule_rows(page) -> None:
    print()
    print("=" * 80)
    print("TABELLEN-CHECK")
    print("=" * 80)

    for selector in ScheduleParser.TABLE_SELECTORS:
        tables = page.locator(selector)
        count = tables.count()

        print(
            f"{selector}: {count}"
        )

        for index in range(count):
            table = tables.nth(index)

            rows = table.locator(
                "tbody > tr"
            ).count()

            headlines = table.locator(
                "tbody > tr.row-headline"
            ).count()

            match_rows = table.locator(
                "tbody > tr:has(td.column-club)"
            ).count()

            print(
                f"  Tabelle {index + 1}: "
                f"Zeilen={rows}, "
                f"Headlines={headlines}, "
                f"Spielzeilen={match_rows}"
            )


def find_print_url(page) -> str:
    links = page.locator(
        "a[href*='spieltagsuebersicht.druck']"
    )

    print()
    print(
        f"Gefundene Druck-Links: "
        f"{links.count()}"
    )

    for index in range(
        links.count()
    ):
        href = links.nth(
            index
        ).get_attribute(
            "href"
        )

        if not href:
            continue

        absolute_url = urljoin(
            page.url,
            href,
        )

        print(
            f"  {index + 1}: {absolute_url}"
        )

        if "/max/999/" in absolute_url:
            return absolute_url

    raise RuntimeError(
        "Kein Druck-Link mit /max/999/ gefunden."
    )


def inspect_parser(page) -> None:
    print()
    print("=" * 80)
    print("SCHEDULEPARSER AUF DRUCKANSICHT")
    print("=" * 80)

    parser = ScheduleParser(
        page
    )

    schedule_data = parser.parse()
    matches = schedule_data.matches

    matchdays = sorted(
        {
            match.matchday
            for match in matches
            if match.matchday is not None
        }
    )

    without_matchday = sum(
        1
        for match in matches
        if match.matchday is None
    )

    teams = sorted(
        {
            team
            for match in matches
            for team in (
                match.home_team,
                match.away_team,
            )
            if team
        }
    )

    print()
    print(
        f"Parser-Spiele: {len(matches)}"
    )
    print(
        f"Mannschaften: {len(teams)}"
    )
    print(
        f"Erkannte Spieltage: {matchdays}"
    )
    print(
        f"Anzahl erkannter Spieltage: "
        f"{len(matchdays)}"
    )
    print(
        f"Spiele ohne Spieltag: "
        f"{without_matchday}"
    )

    print()
    print("ERSTE 10 SPIELE")
    print("-" * 80)

    for match in matches[:10]:
        print(
            f"ST={match.matchday} | "
            f"Nr={match.fixture_number} | "
            f"{match.date} {match.time} | "
            f"{match.home_team} - "
            f"{match.away_team} | "
            f"{match.status}"
        )

    print()
    print("LETZTE 10 SPIELE")
    print("-" * 80)

    for match in matches[-10:]:
        print(
            f"ST={match.matchday} | "
            f"Nr={match.fixture_number} | "
            f"{match.date} {match.time} | "
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

        if browser.page is None:
            raise RuntimeError(
                "Browser-Seite wurde nicht erstellt."
            )

        page = browser.page

        print(
            "Öffne normale Staffel..."
        )

        browser.open(
            url
        )

        page.wait_for_timeout(
            2500
        )

        print()
        print("=" * 80)
        print("NORMALE STAFFEL")
        print("=" * 80)
        print(
            f"URL: {page.url}"
        )

        count_schedule_rows(
            page
        )

        normal_parser = ScheduleParser(
            page
        )
        normal_data = normal_parser.parse()

        print()
        print(
            f"Parser-Spiele normale Ansicht: "
            f"{len(normal_data.matches)}"
        )

        print_url = find_print_url(
            page
        )

        print()
        print("=" * 80)
        print("DRUCKANSICHT")
        print("=" * 80)
        print(
            f"Öffne: {print_url}"
        )

        page.goto(
            print_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_timeout(
            3000
        )

        print(
            f"Aktuelle URL: {page.url}"
        )
        print(
            f"Seitentitel: {page.title()}"
        )

        count_schedule_rows(
            page
        )

        inspect_parser(
            page
        )

        print()
        print("=" * 80)
        print("TEST ABGESCHLOSSEN")
        print("=" * 80)
        print(
            "Browser bleibt 5 Sekunden offen..."
        )

        page.wait_for_timeout(
            5000
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()
