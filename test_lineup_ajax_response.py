from __future__ import annotations

from src.importer.fussballde.browser import FussballDeBrowser


MATCH_EXTERNAL_ID = "02TKDR1UT8000000VS5489BUVUD1610F"

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "borussia-moenchengladbach-fc-bayern-muenchen/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
    "#!/"
)

LINEUP_URL = (
    "https://www.fussball.de/"
    "ajax.match.lineup/"
    "-/mode/PAGE/spiel/"
    f"{MATCH_EXTERNAL_ID}/"
    "ticker-id/selectedTickerId"
)


def main() -> None:
    browser = FussballDeBrowser()

    try:
        browser.start(headless=False)

        if browser.page is None:
            raise RuntimeError("Browserseite fehlt.")

        print("=" * 90)
        print("LINEUP-AJAX ROHANTWORT")
        print("=" * 90)

        print()
        print("1) Normale Spielseite öffnen")
        browser.page.goto(
            MATCH_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        print(f"Page URL:   {browser.page.url}")
        print(f"Page Titel: {browser.page.title()}")

        print()
        print("2) AJAX-Aufstellung abrufen")

        response = browser.page.request.get(
            LINEUP_URL,
            timeout=60_000,
            headers={
                "Referer": browser.page.url,
                "X-Requested-With": "XMLHttpRequest",
            },
        )

        body = response.text()

        print(f"Status:       {response.status}")
        print(f"OK:           {response.ok}")
        print(f"Finale URL:   {response.url}")
        print(
            "Content-Type: "
            f"{response.headers.get('content-type')}"
        )
        print(f"Länge:        {len(body)} Zeichen")

        print()
        print("=" * 90)
        print("ROHANTWORT")
        print("=" * 90)
        print(body)
        print("=" * 90)

        print()
        print("3) Aufstellungsbegriffe auf normaler Seite")
        page_html = browser.page.content()

        for needle in (
            "AUFSTELLUNGEN",
            "Kevin Stöger",
            "Joshua Kimmich",
            "Haris Tabakovic",
        ):
            print(
                f"{needle:<24} "
                f"{'GEFUNDEN' if needle.casefold() in page_html.casefold() else 'NICHT GEFUNDEN'}"
            )

    finally:
        browser.close()


if __name__ == "__main__":
    main()
