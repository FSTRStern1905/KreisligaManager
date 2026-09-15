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

        print()
        print("=" * 80)
        print("STAFFELSPIELPLAN-TEST")
        print("=" * 80)
        print(f"URL: {page.url}")

        print()
        print("TABELLEN")
        print("-" * 80)

        for selector in ScheduleParser.TABLE_SELECTORS:
            tables = page.locator(selector)
            count = tables.count()

            print(f"{selector}: {count}")

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

                links = table.locator(
                    "a[href*='/spiel/']"
                ).count()

                print(
                    f"  Tabelle {index + 1}: "
                    f"Zeilen={rows}, "
                    f"Headlines={headlines}, "
                    f"Spielzeilen={match_rows}, "
                    f"Spiel-Links={links}"
                )

        print()
        print("=" * 80)
        print("SCHEDULEPARSER")
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

        fixture_numbers = [
            match.fixture_number
            for match in matches
            if match.fixture_number is not None
        ]

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
        print(f"Parser-Spiele: {len(matches)}")
        print(f"Mannschaften: {len(teams)}")
        print(
            f"Erkannte Spieltage: {matchdays}"
        )
        print(
            "Spiele ohne Spieltag: "
            f"{sum(m.matchday is None for m in matches)}"
        )
        print(
            "Spiele mit Spielnummer: "
            f"{len(fixture_numbers)}"
        )

        if fixture_numbers:
            print(
                "Spielnummern: "
                f"{min(fixture_numbers)} "
                f"bis {max(fixture_numbers)}"
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

        print()
        print("=" * 80)
        print("TEST ABGESCHLOSSEN")
        print("=" * 80)

        page.wait_for_timeout(5000)

    finally:
        browser.close()


if __name__ == "__main__":
    main()
