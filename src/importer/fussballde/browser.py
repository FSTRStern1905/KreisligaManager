from __future__ import annotations

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


class FussballDeBrowser:

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    def start(
        self,
        headless: bool = True,
    ) -> None:
        if self.playwright is not None:
            return

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=headless,
        )

        self.page = self.browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000,
            }
        )

    def open(
        self,
        url: str,
    ) -> None:
        if self.page is None:
            raise RuntimeError(
                "Browser wurde noch nicht gestartet."
            )

        self.page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        self._accept_cookies()

        try:
            self.page.wait_for_load_state(
                "networkidle",
                timeout=20_000,
            )
        except PlaywrightTimeoutError:
            pass

        self.page.wait_for_timeout(
            3_000
        )

        self.page.evaluate(
            "window.scrollTo(0, document.body.scrollHeight)"
        )

        self.page.wait_for_timeout(
            2_000
        )

        try:
            self.page.wait_for_selector(
                "#fixtures-matchplan-table-matches-table",
                state="attached",
                timeout=30_000,
            )

        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                "Die Spielplan-Tabelle wurde auf der "
                "fussball.de-Seite nicht geladen."
            ) from error

    def _accept_cookies(self) -> None:
        if self.page is None:
            return

        selectors = (
            "button:has-text('Alle akzeptieren')",
            "button:has-text('Akzeptieren')",
            "button:has-text('Zustimmen')",
            "#onetrust-accept-btn-handler",
        )

        for selector in selectors:
            locator = self.page.locator(
                selector
            ).first

            try:
                if locator.is_visible(
                    timeout=1_000
                ):
                    locator.click()
                    self.page.wait_for_timeout(
                        1_000
                    )
                    return

            except PlaywrightTimeoutError:
                continue

    def html(self) -> str:
        if self.page is None:
            raise RuntimeError(
                "Keine Seite geöffnet."
            )

        return self.page.content()

    def title(self) -> str:
        if self.page is None:
            raise RuntimeError(
                "Keine Seite geöffnet."
            )

        return self.page.title()

    def text(
        self,
        selector: str,
    ) -> str:
        if self.page is None:
            raise RuntimeError(
                "Keine Seite geöffnet."
            )

        return (
            self.page
            .locator(selector)
            .first
            .inner_text()
            .strip()
        )

    def exists(
        self,
        selector: str,
    ) -> bool:
        if self.page is None:
            raise RuntimeError(
                "Keine Seite geöffnet."
            )

        return (
            self.page.locator(
                selector
            ).count()
            > 0
        )

    def close(self) -> None:
        if self.page is not None:
            self.page.close()
            self.page = None

        if self.browser is not None:
            self.browser.close()
            self.browser = None

        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None