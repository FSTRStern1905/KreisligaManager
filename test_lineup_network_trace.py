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


def main() -> None:
    browser = FussballDeBrowser()

    try:
        browser.start(headless=False)

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht gestartet werden."
            )

        page = browser.page

        requests: list[str] = []
        responses: list[tuple[int, str]] = []

        def on_request(request) -> None:
            url = request.url.lower()

            if (
                "lineup" in url
                or "aufstellung" in url
                or "ticker" in url
                or "match." in url
            ):
                requests.append(
                    request.url
                )

        def on_response(response) -> None:
            url = response.url.lower()

            if (
                "lineup" in url
                or "aufstellung" in url
                or "ticker" in url
                or "match." in url
            ):
                responses.append(
                    (
                        response.status,
                        response.url,
                    )
                )

        page.on(
            "request",
            on_request,
        )

        page.on(
            "response",
            on_response,
        )

        print("=" * 100)
        print("AUFSTELLUNGS-TAB NETZWERK-DIAGNOSE")
        print("=" * 100)

        page.goto(
            MATCH_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_timeout(
            2500
        )

        print()
        print(
            f"URL: {page.url}"
        )

        print()
        print("=" * 100)
        print("KLICKBARE ELEMENTE MIT 'AUFSTELL'")
        print("=" * 100)

        candidates = page.locator(
            "a, button, li, span, div"
        )

        found = []

        for index in range(
            candidates.count()
        ):
            node = candidates.nth(
                index
            )

            try:
                text = " ".join(
                    node.inner_text().split()
                )
            except Exception:
                continue

            if (
                "aufstell" not in text.casefold()
            ):
                continue

            try:
                tag = node.evaluate(
                    "el => el.tagName"
                )
            except Exception:
                tag = "?"

            try:
                cls = node.get_attribute(
                    "class"
                )
            except Exception:
                cls = None

            try:
                href = node.get_attribute(
                    "href"
                )
            except Exception:
                href = None

            found.append(
                (
                    index,
                    tag,
                    text[:120],
                    cls,
                    href,
                )
            )

        for item in found[:40]:
            print(
                f"idx={item[0]} | "
                f"tag={item[1]} | "
                f"text={item[2]!r} | "
                f"class={item[3]!r} | "
                f"href={item[4]!r}"
            )

        print()
        print("=" * 100)
        print("AUFSTELLUNGS-TAB ANKLICKEN")
        print("=" * 100)

        clicked = False

        selectors = (
            "text=Aufstellungen",
            "text=AUFSTELLUNGEN",
            "a:has-text('Aufstellungen')",
            "button:has-text('Aufstellungen')",
            "[data-ng-click*='lineup']",
            "[href*='lineup']",
        )

        for selector in selectors:
            locator = page.locator(
                selector
            )

            if locator.count() == 0:
                continue

            for index in range(
                locator.count()
            ):
                node = locator.nth(
                    index
                )

                try:
                    if not node.is_visible():
                        continue

                    print(
                        f"Klicke: {selector} "
                        f"(Treffer {index})"
                    )

                    node.click(
                        timeout=5000,
                    )

                    clicked = True

                    page.wait_for_timeout(
                        3000
                    )

                    break

                except Exception as exc:
                    print(
                        f"  Klick fehlgeschlagen: "
                        f"{type(exc).__name__}: {exc}"
                    )

            if clicked:
                break

        print()
        print(
            f"Klick erfolgreich: {clicked}"
        )

        print()
        print("=" * 100)
        print("REQUESTS")
        print("=" * 100)

        seen = set()

        for url in requests:
            if url in seen:
                continue

            seen.add(
                url
            )

            print(
                url
            )

        print()
        print("=" * 100)
        print("RESPONSES")
        print("=" * 100)

        seen_response = set()

        for status, url in responses:
            key = (
                status,
                url,
            )

            if key in seen_response:
                continue

            seen_response.add(
                key
            )

            print(
                f"{status} | {url}"
            )

        print()
        print("=" * 100)
        print("DOM NACH KLICK")
        print("=" * 100)

        selectors_after = (
            ".match-lineup",
            ".player-wrapper",
            ".player-name",
            "[class*='lineup']",
        )

        for selector in selectors_after:
            print(
                f"{selector:<24} "
                f"{page.locator(selector).count()}"
            )

        body_text = page.locator(
            "body"
        ).inner_text()

        for name in (
            "Kevin Stöger",
            "Haris Tabakovic",
            "Joshua Kimmich",
            "Harry Edward Kane",
        ):
            print(
                f"{name:<25} "
                f"{'JA' if name.casefold() in body_text.casefold() else 'NEIN'}"
            )

        print()
        print("=" * 100)
        print("TEST ENDE")
        print("=" * 100)

    finally:
        browser.close()


if __name__ == "__main__":
    main()
