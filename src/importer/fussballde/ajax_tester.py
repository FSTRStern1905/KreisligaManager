from __future__ import annotations

import json
import sys

from playwright.sync_api import Response

from src.importer.fussballde.browser import FussballDeBrowser


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.ajax_tester "
            "\"https://www.fussball.de/spielplan/...\""
        )
        sys.exit(1)

    url = sys.argv[1]

    browser = FussballDeBrowser()

    responses: list[Response] = []

    def response_listener(response: Response) -> None:
        response_url = response.url.lower()

        if (
            "ajax" in response_url
            or "fixture" in response_url
            or "matchplan" in response_url
            or "spielplan" in response_url
            or "staffel" in response_url
        ):
            responses.append(response)

    try:
        browser.start()

        if browser.page is None:
            raise RuntimeError("Browser wurde nicht gestartet.")

        browser.page.on("response", response_listener)

        browser.open(url)

        browser.page.wait_for_timeout(5000)

        print()
        print("=" * 80)
        print(f"Gefundene Responses: {len(responses)}")
        print("=" * 80)

        for i, response in enumerate(responses, start=1):

            print()
            print("-" * 80)
            print(f"[{i}] {response.status} {response.url}")

            try:
                content_type = response.headers.get("content-type", "")
            except Exception:
                content_type = ""

            print(f"Content-Type: {content_type}")

            try:

                if "json" in content_type:
                    data = response.json()

                    print("\nJSON Vorschau:\n")
                    print(
                        json.dumps(
                            data,
                            ensure_ascii=False,
                            indent=2,
                        )[:3000]
                    )

                else:

                    text = response.text()

                    print("\nText Vorschau:\n")
                    print(text[:3000])

            except Exception as exc:
                print(exc)

    finally:
        browser.close()


if __name__ == "__main__":
    main()