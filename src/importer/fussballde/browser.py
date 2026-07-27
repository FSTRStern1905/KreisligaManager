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

    PAGE_TYPE_AUTO = "auto"
    PAGE_TYPE_SCHEDULE = "schedule"
    PAGE_TYPE_MATCH_DETAIL = "match_detail"
    PAGE_TYPE_GENERIC = "generic"

    TABLE_SELECTORS = (
        "#fixtures-matchplan-table-matches-table",
        "table[id*='fixtures-matchplan']",
        ".fixtures-matchplan-table",
        "table:has(td.column-club)",
    )

    MATCH_DETAIL_SELECTORS = (
        "main",
        "#stage",
        ".stage",
        "[class*='match-detail']",
        "[class*='matchcenter']",
        "[class*='match-center']",
        "[class*='game-detail']",
        "[class*='fixture-detail']",
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
        page_type: str = PAGE_TYPE_AUTO,
    ) -> None:
        if self.page is None:
            raise RuntimeError(
                "Browser wurde noch nicht gestartet."
            )

        resolved_page_type = self._resolve_page_type(
            url=url,
            page_type=page_type,
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

        self._scroll_page()

        if resolved_page_type == self.PAGE_TYPE_SCHEDULE:
            self._wait_for_schedule_table()

        elif resolved_page_type == self.PAGE_TYPE_MATCH_DETAIL:
            self._wait_for_match_detail()

        else:
            self._wait_for_generic_content()

    def _resolve_page_type(
        self,
        url: str,
        page_type: str,
    ) -> str:
        allowed_page_types = {
            self.PAGE_TYPE_AUTO,
            self.PAGE_TYPE_SCHEDULE,
            self.PAGE_TYPE_MATCH_DETAIL,
            self.PAGE_TYPE_GENERIC,
        }

        if page_type not in allowed_page_types:
            raise ValueError(
                f"Unbekannter Seitentyp: {page_type}"
            )

        if page_type != self.PAGE_TYPE_AUTO:
            return page_type

        normalized_url = url.casefold()

        if "/spieltag/" in normalized_url:
            return self.PAGE_TYPE_SCHEDULE

        if "/spiel/" in normalized_url:
            return self.PAGE_TYPE_MATCH_DETAIL

        return self.PAGE_TYPE_GENERIC

    def _scroll_page(self) -> None:
        if self.page is None:
            return

        self.page.evaluate(
            """
            async () => {
                const delay = (milliseconds) => {
                    return new Promise(
                        resolve => setTimeout(
                            resolve,
                            milliseconds
                        )
                    );
                };

                const maximumHeight =
                    document.body.scrollHeight;

                const step = 700;

                for (
                    let position = 0;
                    position < maximumHeight;
                    position += step
                ) {
                    window.scrollTo(0, position);
                    await delay(150);
                }

                window.scrollTo(
                    0,
                    document.body.scrollHeight
                );
            }
            """
        )

        self.page.wait_for_timeout(2_000)

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

        if self._wait_for_any_selector(
            selectors=self.TABLE_SELECTORS,
            timeout_per_selector=10_000,
        ):
            return

        raise RuntimeError(
            "Die Spielplan-Tabelle wurde auf der "
            "fussball.de-Seite nicht geladen."
        )

    def _wait_for_match_detail(self) -> None:
        if self.page is None:
            return

        if self._wait_for_any_selector(
            selectors=self.MATCH_DETAIL_SELECTORS,
            timeout_per_selector=5_000,
        ):
            return

        self._wait_for_generic_content()

    def _wait_for_generic_content(self) -> None:
        if self.page is None:
            return

        try:
            self.page.wait_for_selector(
                "body",
                state="attached",
                timeout=10_000,
            )
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                "Die fussball.de-Seite wurde nicht geladen."
            ) from error

    def _wait_for_any_selector(
        self,
        selectors: tuple[str, ...],
        timeout_per_selector: int,
    ) -> bool:
        if self.page is None:
            return False

        for selector in selectors:
            try:
                self.page.wait_for_selector(
                    selector,
                    state="attached",
                    timeout=timeout_per_selector,
                )

                return True

            except PlaywrightTimeoutError:
                continue

        return False

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