from __future__ import annotations

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.parsers.match_detail_parser import (
    MatchDetailParser,
)


MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "sv-trier-irsch-sv-foehren/-/spiel/"
    "02TNB07C34000000VS5489BUVSSD35NB"
)


def main() -> None:
    browser = FussballDeBrowser()

    try:
        browser.start(
            headless=False,
        )

        browser.open(
            MATCH_URL
        )

        if browser.page is None:
            raise RuntimeError(
                "Die Spielseite wurde nicht geladen."
            )

        html = browser.page.content()

        parser = MatchDetailParser(
            browser.page
        )

        data = parser.parse(
            html=html,
            source_url=MATCH_URL,
        )

        print()
        print("=" * 60)
        print("MATCH DETAIL DATA")
        print("=" * 60)
        print(f"Spiel-ID: {data.match_id!r}")
        print(f"Heim: {data.home_team!r}")
        print(f"Auswärts: {data.away_team!r}")
        print(
            f"Ergebnis: "
            f"{data.home_goals}:"
            f"{data.away_goals}"
        )
        print(
            f"Halbzeit: "
            f"{data.halftime_home}:"
            f"{data.halftime_away}"
        )
        print(f"Stadion: {data.stadium!r}")
        print(f"Schiedsrichter: {data.referee!r}")
        print(f"Zuschauer: {data.attendance!r}")
        print(f"Events: {len(data.events)}")

        output_path = (
            "data/temp/"
            "inspect_match_detail_page.html"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(html)

        print()
        print(
            f"HTML gespeichert unter: "
            f"{output_path}"
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()