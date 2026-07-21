from __future__ import annotations

from playwright.sync_api import Browser, Page, Playwright, sync_playwright


class FussballDeBrowser:
    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    def start(self, headless: bool = True) -> None:
        if self.playwright is not None:
            return

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def open(self, url: str) -> None:
        if self.page is None:
            raise RuntimeError("Browser wurde noch nicht gestartet.")

        self.page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        self.page.wait_for_timeout(3000)

    def html(self) -> str:
        if self.page is None:
            raise RuntimeError("Keine Seite geöffnet.")

        return self.page.content()

    def title(self) -> str:
        if self.page is None:
            raise RuntimeError("Keine Seite geöffnet.")

        return self.page.title()

    def text(self, selector: str) -> str:
        if self.page is None:
            raise RuntimeError("Keine Seite geöffnet.")

        return (
            self.page
            .locator(selector)
            .first
            .inner_text()
            .strip()
        )

    def exists(self, selector: str) -> bool:
        if self.page is None:
            raise RuntimeError("Keine Seite geöffnet.")

        return self.page.locator(selector).count() > 0

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