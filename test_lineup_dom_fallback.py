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

TARGET_NAMES = (
    "Kevin Stöger",
    "Haris Tabakovic",
    "Rocco Reitz",
    "Joshua Kimmich",
    "Harry Edward Kane",
    "Nicolas Jackson",
)


def normalize(value: str | None) -> str:
    return " ".join(
        (value or "").casefold().split()
    )


def main() -> None:
    browser = FussballDeBrowser()

    try:
        browser.start(headless=False)

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht gestartet werden."
            )

        page = browser.page

        print("=" * 96)
        print("LINEUP-DOM-FALLBACK-TEST")
        print("=" * 96)

        page.goto(
            MATCH_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_timeout(2500)

        print()
        print(f"URL:   {page.url}")
        print(f"Titel: {page.title()}")

        selectors = [
            ".match-lineup",
            ".lineup",
            ".player-wrapper",
            ".player-name",
            "[class*='lineup']",
        ]

        print()
        print("=" * 96)
        print("DOM-SELECTOR-CHECK")
        print("=" * 96)

        for selector in selectors:
            try:
                count = page.locator(selector).count()
            except Exception:
                count = -1

            print(
                f"{selector:<24} {count}"
            )

        print()
        print("=" * 96)
        print("BEKANNTE SPIELER IM GERENDERTEN DOM")
        print("=" * 96)

        body_text = page.locator("body").inner_text()

        for target in TARGET_NAMES:
            found = (
                normalize(target)
                in normalize(body_text)
            )

            print(
                f"{target:<28} "
                f"{'JA' if found else 'NEIN'}"
            )

        print()
        print("=" * 96)
        print("SPIELER-ELEMENTE")
        print("=" * 96)

        player_nodes = page.locator(
            ".player-wrapper"
        )

        player_count = player_nodes.count()

        print(
            f".player-wrapper gesamt: "
            f"{player_count}"
        )

        found_players: list[str] = []

        for index in range(player_count):
            node = player_nodes.nth(index)

            try:
                text = " ".join(
                    node.inner_text().split()
                )
            except Exception:
                text = ""

            if text:
                found_players.append(text)

        if found_players:
            for index, text in enumerate(
                found_players,
                start=1,
            ):
                print(
                    f"{index:>2}. {text}"
                )
        else:
            print(
                "Keine .player-wrapper-Elemente gefunden."
            )

        print()
        print("=" * 96)
        print("AUFSTELLUNGS-CONTAINER")
        print("=" * 96)

        possible = page.locator(
            "[class*='lineup'], "
            "[class*='formation'], "
            "[class*='aufstellung']"
        )

        possible_count = possible.count()

        print(
            f"Mögliche Container: "
            f"{possible_count}"
        )

        for index in range(
            min(possible_count, 40)
        ):
            node = possible.nth(index)

            try:
                cls = node.get_attribute(
                    "class"
                )
                text = " ".join(
                    node.inner_text().split()
                )
            except Exception:
                continue

            if not text:
                continue

            print()
            print(
                f"[{index}] class={cls}"
            )
            print(
                text[:500]
            )

        print()
        print("=" * 96)
        print("HTML-AUSSCHNITTE ZU ZIELSPIELERN")
        print("=" * 96)

        html = page.content()

        for target in TARGET_NAMES:
            needle = target.split()[-1]
            pos = normalize(html).find(
                normalize(needle)
            )

            print()
            print(
                f"{target}: "
                f"{'gefunden' if pos >= 0 else 'nicht gefunden'}"
            )

            if pos >= 0:
                start = max(
                    0,
                    pos - 350,
                )
                end = min(
                    len(html),
                    pos + 700,
                )

                snippet = html[
                    start:end
                ].replace(
                    "\n",
                    " ",
                )

                print(
                    " ".join(
                        snippet.split()
                    )
                )

        print()
        print("=" * 96)
        print("TEST ENDE")
        print("=" * 96)

    finally:
        browser.close()


if __name__ == "__main__":
    main()
