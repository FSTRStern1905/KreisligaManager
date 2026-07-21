from src.importer.fussballde.browser import FussballDeBrowser


TEAM_URL = (
    "https://www.fussball.de/mannschaft/"
    "fsg-ehrang-pfalzel-sv-ehrang-rheinland/-/"
    "saison/2627/team-id/011MIE1LO0000000VTVG0001VTR8C1K7#!/"
)


def main() -> None:
    browser = FussballDeBrowser()

    try:
        browser.start(headless=False)
        browser.open(TEAM_URL)

        html = browser.html()

        print("=" * 60)
        print(f"Titel: {browser.title()}")
        print(f"HTML-Länge: {len(html):,} Zeichen")
        print(f"URL: {TEAM_URL}")
        print("=" * 60)

    finally:
        browser.close()


if __name__ == "__main__":
    main()