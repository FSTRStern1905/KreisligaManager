from __future__ import annotations

from playwright.sync_api import (
    Browser,
    Frame,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


class FussballDeBrowser:

    TABLE_SELECTORS = (
        "#fixtures-matchplan-table-matches-table",
        "table[id*='fixtures-matchplan']",
        ".fixtures-matchplan-table",
        "table:has(td.column-club)",
    )

    COOKIE_SELECTORS = (
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Akzeptieren und weiter')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Zustimmen')",
        "button:has-text('Einverstanden')",
        "button[title*='akzeptieren' i]",
        "button[aria-label*='akzeptieren' i]",
        "#onetrust-accept-btn-handler",
        "[data-testid*='accept' i]",
        "[class*='accept' i] button",
    )

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

        self.page.wait_for_timeout(2_000)

        self.page.evaluate(
            "window.scrollTo(0, document.body.scrollHeight)"
        )

        self.page.wait_for_timeout(2_000)

        self._wait_for_schedule_table()

    def _accept_cookies(self) -> None:
        if self.page is None:
            return

        self.page.wait_for_timeout(1_500)

        if self._click_cookie_button_in_frame(
            self.page.main_frame
        ):
            self.page.wait_for_timeout(2_000)
            return

        for frame in self.page.frames:
            if frame == self.page.main_frame:
                continue

            if self._click_cookie_button_in_frame(frame):
                self.page.wait_for_timeout(2_000)
                return

    def _click_cookie_button_in_frame(
        self,
        frame: Frame,
    ) -> bool:
        for selector in self.COOKIE_SELECTORS:
            locator = frame.locator(selector).first

            try:
                if locator.count() == 0:
                    continue

                if not locator.is_visible(
                    timeout=1_000
                ):
                    continue

                locator.click(
                    timeout=3_000,
                    force=True,
                )

                return True

            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue

        return False

    def _wait_for_schedule_table(self) -> None:
        if self.page is None:
            return

        for selector in self.TABLE_SELECTORS:
            try:
                self.page.wait_for_selector(
                    selector,
                    state="attached",
                    timeout=10_000,
                )

                return

            except PlaywrightTimeoutError:
                continue

        raise RuntimeError(
            "Die Spielplan-Tabelle wurde auf der "
            "fussball.de-Seite nicht geladen."
        )

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