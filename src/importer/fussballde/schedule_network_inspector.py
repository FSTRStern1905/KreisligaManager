from __future__ import annotations

import sys
from datetime import datetime
from urllib.parse import parse_qsl, urlparse

from src.importer.fussballde.browser import FussballDeBrowser


DEFAULT_URL = (
    "https://www.fussball.de/spieltagsuebersicht/"
    "rheinlandliga-herren-rheinland-rheinlandliga-herren-"
    "saison2627-rheinland/-/staffel/"
    "031AU2ESDK00000IVS5489BUVV628VP4-G#!/"
)

INTERESTING_KEYWORDS = (
    "fixture",
    "match",
    "spiel",
    "staffel",
    "competition",
    "date",
    "from",
    "to",
    "ajax",
)

IGNORED_HOST_PARTS = (
    "doubleclick",
    "googlesyndication",
    "googleadservices",
    "google-analytics",
    "googletagmanager",
    "adform",
    "criteo",
    "yieldlab",
    "rubiconproject",
    "pubmatic",
    "adnxs",
    "amazon-adsystem",
    "facebook",
    "quantserve",
)


def is_ignored(url: str) -> bool:
    host = urlparse(url).netloc.casefold()

    return any(
        part in host
        for part in IGNORED_HOST_PARTS
    )


def is_interesting(url: str) -> bool:
    if is_ignored(url):
        return False

    normalized = url.casefold()

    if "fussball.de" in normalized:
        return True

    return any(
        keyword in normalized
        for keyword in INTERESTING_KEYWORDS
    )


def safe_post_data(request) -> str | None:
    """
    post_data kann bei einzelnen Requests binäre Daten enthalten.
    Der Inspector darf daran niemals abbrechen.
    """
    try:
        value = request.post_data

        if not value:
            return None

        return value[:3000]

    except (UnicodeDecodeError, UnicodeError):
        return "<binäre POST-Daten>"

    except Exception as error:
        return (
            "<POST-Daten nicht lesbar: "
            f"{type(error).__name__}>"
        )


def print_request(request) -> None:
    url = request.url

    if not is_interesting(url):
        return

    print()
    print("-" * 80)
    print(
        f"REQUEST {request.method} | "
        f"{request.resource_type}"
    )
    print(url)

    parsed = urlparse(url)

    if parsed.query:
        print("QUERY:")

        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):
            print(
                f"  {key} = {value}"
            )

    if request.method.upper() != "GET":
        post_data = safe_post_data(
            request
        )

        if post_data:
            print("POST-DATA:")
            print(
                post_data
            )


def print_response(response) -> None:
    url = response.url

    if not is_interesting(url):
        return

    try:
        content_type = response.headers.get(
            "content-type",
            "",
        )
    except Exception:
        content_type = ""

    print(
        f"RESPONSE {response.status} | "
        f"{content_type or '-'}"
    )


def inspect_dom(page) -> None:
    print()
    print("=" * 80)
    print("DOM: AJAX / SPIELPLAN-RELEVANTE ELEMENTE")
    print("=" * 80)

    result = page.evaluate(
        """
        () => {
            const nodes = Array.from(
                document.querySelectorAll(
                    '[data-ajax-resource], '
                    + '[data-url], '
                    + '[data-href], '
                    + '[data-from], '
                    + '[data-to], '
                    + '[data-date], '
                    + 'form, '
                    + 'a[href], '
                    + 'button'
                )
            );

            const words = [
                'fixture',
                'match',
                'spiel',
                'staffel',
                'competition',
                'date',
                'ajax',
                'zurück',
                'weiter'
            ];

            const rows = [];

            for (const node of nodes) {
                const attrs = {};

                for (const attr of node.attributes || []) {
                    const name = attr.name.toLowerCase();

                    if (
                        name.startsWith('data-')
                        || name === 'action'
                        || name === 'href'
                        || name === 'id'
                        || name === 'name'
                        || name === 'class'
                    ) {
                        attrs[name] = attr.value;
                    }
                }

                const text = (
                    node.innerText
                    || node.textContent
                    || ''
                )
                    .replace(/\\s+/g, ' ')
                    .trim()
                    .slice(0, 300);

                const haystack = (
                    JSON.stringify(attrs)
                    + ' '
                    + text
                ).toLowerCase();

                if (
                    words.some(
                        word => haystack.includes(word)
                    )
                ) {
                    rows.push({
                        tag: node.tagName,
                        attrs,
                        text
                    });
                }
            }

            return rows.slice(0, 300);
        }
        """
    )

    print(
        f"Gefundene relevante DOM-Elemente: "
        f"{len(result)}"
    )

    for index, item in enumerate(
        result,
        start=1,
    ):
        print()
        print(
            f"[{index}] {item['tag']}"
        )

        for key, value in item[
            "attrs"
        ].items():
            print(
                f"  {key}: {value}"
            )

        if item["text"]:
            print(
                f"  text: {item['text']}"
            )


def inspect_resources(page) -> None:
    print()
    print("=" * 80)
    print("PERFORMANCE RESOURCE URLs")
    print("=" * 80)

    resources = page.evaluate(
        """
        () => performance
            .getEntriesByType('resource')
            .map(entry => entry.name)
        """
    )

    filtered = [
        resource
        for resource in resources
        if is_interesting(
            resource
        )
    ]

    print(
        f"Relevante Resources: {len(filtered)}"
    )

    for resource in filtered:
        print(
            resource
        )


def inspect_buttons(page) -> None:
    print()
    print("=" * 80)
    print("NAVIGATION / BUTTONS / LINKS")
    print("=" * 80)

    items = page.evaluate(
        """
        () => Array.from(
            document.querySelectorAll(
                'button, a[href], input[type="submit"]'
            )
        ).map(node => ({
            tag: node.tagName,
            text: (
                node.innerText
                || node.value
                || node.getAttribute('title')
                || node.getAttribute('aria-label')
                || ''
            )
                .replace(/\\s+/g, ' ')
                .trim()
                .slice(0, 200),
            href: node.getAttribute('href'),
            id: node.id || null,
            cls: node.className || null,
            dataAjax: node.getAttribute(
                'data-ajax-resource'
            )
        })).filter(item => {
            const value = (
                (item.text || '')
                + ' '
                + (item.href || '')
                + ' '
                + (item.id || '')
                + ' '
                + (item.cls || '')
                + ' '
                + (item.dataAjax || '')
            ).toLowerCase();

            return [
                'spiel',
                'match',
                'fixture',
                'staffel',
                'date',
                'weiter',
                'zurück',
                'vor',
                'next',
                'prev',
                'ajax'
            ].some(word => value.includes(word));
        }).slice(0, 200)
        """
    )

    print(
        f"Gefundene Kandidaten: {len(items)}"
    )

    for index, item in enumerate(
        items,
        start=1,
    ):
        print()
        print(
            f"[{index}] {item['tag']}"
        )
        print(
            f"  text: {item['text']!r}"
        )
        print(
            f"  href: {item['href']!r}"
        )
        print(
            f"  id: {item['id']!r}"
        )
        print(
            f"  class: {item['cls']!r}"
        )
        print(
            f"  data-ajax-resource: "
            f"{item['dataAjax']!r}"
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

        page.on(
            "request",
            print_request,
        )

        page.on(
            "response",
            print_response,
        )

        print()
        print("=" * 80)
        print("NETWORK-INSPECTOR V2")
        print("=" * 80)
        print(
            "Start:",
            datetime.now().isoformat(
                timespec="seconds"
            ),
        )
        print(
            "Öffne Staffel..."
        )

        browser.open(
            url
        )

        page.wait_for_timeout(
            3000
        )

        inspect_dom(
            page
        )
        inspect_buttons(
            page
        )
        inspect_resources(
            page
        )

        print()
        print("=" * 80)
        print("LIVE-PHASE")
        print("=" * 80)
        print(
            "Browser bleibt 15 Sekunden offen."
        )
        print(
            "Falls du Spielplan-Navigation, "
            "Datumswahl, Zurück/Weiter oder ähnliche "
            "Elemente siehst: jetzt anklicken."
        )
        print(
            "Die Requests werden weiter protokolliert."
        )

        page.wait_for_timeout(
            15000
        )

        print()
        print("=" * 80)
        print("RESOURCES NACH LIVE-PHASE")
        print("=" * 80)

        inspect_resources(
            page
        )

        print()
        print("=" * 80)
        print("INSPEKTOR ABGESCHLOSSEN")
        print("=" * 80)

    finally:
        browser.close()


if __name__ == "__main__":
    main()
