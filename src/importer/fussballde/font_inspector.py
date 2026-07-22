from __future__ import annotations

import sys
from urllib.parse import urljoin

from src.importer.fussballde.browser import FussballDeBrowser


FONT_EXTENSIONS = (
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
)

STYLE_EXTENSIONS = (
    ".css",
)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.font_inspector "
            "\"https://www.fussball.de/spielplan/...\""
        )
        sys.exit(1)

    url = sys.argv[1]
    browser = FussballDeBrowser()

    font_urls: set[str] = set()
    stylesheet_urls: set[str] = set()

    try:
        browser.start()

        if browser.page is None:
            raise RuntimeError("Browser wurde nicht gestartet.")

        page = browser.page

        def handle_response(response) -> None:
            response_url = response.url
            clean_url = response_url.split("?")[0].lower()

            content_type = response.headers.get(
                "content-type",
                "",
            ).lower()

            if (
                clean_url.endswith(FONT_EXTENSIONS)
                or "font/" in content_type
                or "application/font" in content_type
            ):
                font_urls.add(response_url)

            if (
                clean_url.endswith(STYLE_EXTENSIONS)
                or "text/css" in content_type
            ):
                stylesheet_urls.add(response_url)

        page.on("response", handle_response)

        print("Seite wird geladen ...")
        browser.open(url)

        page.wait_for_timeout(5000)

        print()
        print("=" * 80)
        print("GELADENE SCHRIFTARTEN")
        print("=" * 80)

        if not font_urls:
            print("Keine Schriftdateien über Netzwerk-Responses gefunden.")
        else:
            for index, font_url in enumerate(
                sorted(font_urls),
                start=1,
            ):
                print(f"[{index}] {font_url}")

        print()
        print("=" * 80)
        print("GELADENE STYLESHEETS")
        print("=" * 80)

        if not stylesheet_urls:
            print("Keine Stylesheets gefunden.")
        else:
            for index, stylesheet_url in enumerate(
                sorted(stylesheet_urls),
                start=1,
            ):
                print(f"[{index}] {stylesheet_url}")

        print()
        print("=" * 80)
        print("FONT-FACE REGELN AUS DEM GERENDERTEN DOKUMENT")
        print("=" * 80)

        font_faces = page.evaluate(
            """
            () => {
                const results = [];

                for (const styleSheet of document.styleSheets) {
                    let rules;

                    try {
                        rules = styleSheet.cssRules;
                    } catch (error) {
                        continue;
                    }

                    if (!rules) {
                        continue;
                    }

                    for (const rule of rules) {
                        if (
                            rule.type === CSSRule.FONT_FACE_RULE
                        ) {
                            results.push({
                                stylesheet:
                                    styleSheet.href || "inline",
                                cssText: rule.cssText
                            });
                        }
                    }
                }

                return results;
            }
            """
        )

        if not font_faces:
            print("Keine direkt lesbaren @font-face-Regeln gefunden.")
        else:
            for index, font_face in enumerate(
                font_faces,
                start=1,
            ):
                print()
                print(f"[{index}]")
                print(
                    f"Stylesheet: "
                    f"{font_face.get('stylesheet', '')}"
                )
                print(font_face.get("cssText", ""))

        print()
        print("=" * 80)
        print("VERWENDETE SCHRIFTARTEN IN SPIELZEILEN")
        print("=" * 80)

        font_usage = page.evaluate(
            """
            () => {
                const rows = document.querySelectorAll(
                    "#fixtures-matchplan-table-matches-table "
                    + "tbody > tr"
                );

                const results = [];
                const seen = new Set();

                for (const row of rows) {
                    const elements = [
                        row,
                        ...row.querySelectorAll("*")
                    ];

                    for (const element of elements) {
                        const text =
                            element.textContent?.trim() || "";

                        if (!text) {
                            continue;
                        }

                        const style =
                            window.getComputedStyle(element);

                        const key = [
                            element.tagName,
                            element.className,
                            style.fontFamily,
                            style.fontWeight,
                            style.fontStyle
                        ].join("|");

                        if (seen.has(key)) {
                            continue;
                        }

                        seen.add(key);

                        results.push({
                            tag: element.tagName,
                            className:
                                typeof element.className === "string"
                                    ? element.className
                                    : "",
                            fontFamily: style.fontFamily,
                            fontWeight: style.fontWeight,
                            fontStyle: style.fontStyle,
                            text: text.slice(0, 100)
                        });
                    }

                    if (results.length >= 100) {
                        break;
                    }
                }

                return results;
            }
            """
        )

        for index, usage in enumerate(font_usage, start=1):
            print()
            print(f"[{index}]")
            print(
                f"Element: {usage.get('tag', '')} "
                f"class=\"{usage.get('className', '')}\""
            )
            print(
                f"Font: {usage.get('fontFamily', '')} "
                f"| Gewicht: {usage.get('fontWeight', '')} "
                f"| Stil: {usage.get('fontStyle', '')}"
            )
            print(f"Text: {usage.get('text', '')}")

    finally:
        browser.close()


if __name__ == "__main__":
    main()