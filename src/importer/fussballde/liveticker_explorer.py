from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)


@dataclass(slots=True)
class LivetickerExplorerResult:
    source_url: str
    match_id: str
    page_title: str
    ticker_available: bool
    ticker_selectors_found: tuple[str, ...]
    ticker_links_found: tuple[str, ...]
    event_rows_found: int
    timeline_events_found: int
    html_path: str
    report_path: str

    def to_dict(self) -> dict:
        return asdict(self)


class LivetickerExplorer:
    DEBUG_DIRECTORY = Path(
        "debug/liveticker"
    )

    TICKER_SELECTORS = (
        "#liveticker",
        "#live-ticker",
        ".liveticker",
        ".live-ticker",
        "[class*='liveticker']",
        "[class*='live-ticker']",
        "[data-liveticker]",
        "[data-live-ticker]",
        "[data-ticker]",
    )

    TICKER_LINK_PATTERNS = (
        "liveticker",
        "live-ticker",
        "ticker",
        "spielbericht",
    )

    EVENT_SELECTORS = (
        ".row-event",
        ".ticker-event",
        ".liveticker-event",
        ".live-ticker-event",
        "[class*='ticker-event']",
        "[data-event-type]",
    )

    def explore(
        self,
        url: str,
        headless: bool = True,
    ) -> LivetickerExplorerResult:
        normalized_url = url.strip()

        if not normalized_url:
            raise ValueError(
                "Die Spiel-URL darf nicht leer sein."
            )

        browser = FussballDeBrowser()

        try:
            browser.start(
                headless=headless,
            )

            browser.open(
                normalized_url,
                page_type=(
                    FussballDeBrowser
                    .PAGE_TYPE_MATCH_DETAIL
                ),
            )

            html = browser.html()
            title = browser.title().strip()

            result = self.explore_html(
                html=html,
                source_url=normalized_url,
                page_title=title,
            )

            return result

        finally:
            browser.close()

    def explore_html(
        self,
        html: str,
        source_url: str = "",
        page_title: str = "",
    ) -> LivetickerExplorerResult:
        if not html.strip():
            raise ValueError(
                "Das HTML darf nicht leer sein."
            )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        match_id = self._extract_match_id(
            source_url=source_url,
            soup=soup,
        )

        if not match_id:
            match_id = "unknown_match"

        if not page_title:
            title_element = soup.select_one(
                "title"
            )

            if title_element is not None:
                page_title = (
                    title_element.get_text(
                        " ",
                        strip=True,
                    )
                )

        selectors_found = (
            self._find_ticker_selectors(
                soup
            )
        )

        ticker_links = self._find_ticker_links(
            soup
        )

        event_rows_found = (
            self._count_event_rows(
                soup
            )
        )

        timeline_events_found = (
            self._count_timeline_events(
                soup
            )
        )

        ticker_available = bool(
            selectors_found
            or ticker_links
            or self._contains_ticker_text(
                soup
            )
        )

        html_path = self._save_html(
            match_id=match_id,
            html=html,
        )

        result = LivetickerExplorerResult(
            source_url=source_url,
            match_id=match_id,
            page_title=page_title,
            ticker_available=ticker_available,
            ticker_selectors_found=tuple(
                selectors_found
            ),
            ticker_links_found=tuple(
                ticker_links
            ),
            event_rows_found=(
                event_rows_found
            ),
            timeline_events_found=(
                timeline_events_found
            ),
            html_path=str(
                html_path
            ),
            report_path="",
        )

        report_path = self._save_report(
            result
        )

        result.report_path = str(
            report_path
        )

        self._print_result(
            result
        )

        return result

    def _find_ticker_selectors(
        self,
        soup: BeautifulSoup,
    ) -> list[str]:
        selectors_found: list[str] = []

        for selector in self.TICKER_SELECTORS:
            if soup.select_one(
                selector
            ) is not None:
                selectors_found.append(
                    selector
                )

        return selectors_found

    def _find_ticker_links(
        self,
        soup: BeautifulSoup,
    ) -> list[str]:
        links: list[str] = []

        for link in soup.select(
            "a[href]"
        ):
            href = str(
                link.get(
                    "href",
                    "",
                )
                or ""
            ).strip()

            link_text = (
                link.get_text(
                    " ",
                    strip=True,
                )
                .casefold()
            )

            normalized_href = href.casefold()

            if not any(
                pattern in normalized_href
                or pattern in link_text
                for pattern
                in self.TICKER_LINK_PATTERNS
            ):
                continue

            if href and href not in links:
                links.append(
                    href
                )

        return links

    def _count_event_rows(
        self,
        soup: BeautifulSoup,
    ) -> int:
        event_elements: set[int] = set()

        for selector in self.EVENT_SELECTORS:
            for element in soup.select(
                selector
            ):
                event_elements.add(
                    id(element)
                )

        return len(
            event_elements
        )

    @staticmethod
    def _count_timeline_events(
        soup: BeautifulSoup,
    ) -> int:
        timeline = soup.select_one(
            "[data-match-events]"
        )

        if timeline is None:
            return 0

        raw_value = str(
            timeline.get(
                "data-match-events",
                "",
            )
            or ""
        )

        return len(
            re.findall(
                r"['\"]type['\"]\s*:",
                raw_value,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _contains_ticker_text(
        soup: BeautifulSoup,
    ) -> bool:
        page_text = (
            soup.get_text(
                " ",
                strip=True,
            )
            .casefold()
        )

        return any(
            keyword in page_text
            for keyword in (
                "liveticker",
                "live-ticker",
                "live ticker",
            )
        )

    def _save_html(
        self,
        match_id: str,
        html: str,
    ) -> Path:
        self.DEBUG_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            self.DEBUG_DIRECTORY
            / f"{match_id}.html"
        )

        path.write_text(
            html,
            encoding="utf-8",
        )

        return path

    def _save_report(
        self,
        result: LivetickerExplorerResult,
    ) -> Path:
        self.DEBUG_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            self.DEBUG_DIRECTORY
            / f"{result.match_id}.json"
        )

        path.write_text(
            json.dumps(
                result.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return path

    @staticmethod
    def _print_result(
        result: LivetickerExplorerResult,
    ) -> None:
        print("=" * 70)
        print("FUSSBALL.DE LIVETICKER EXPLORER")
        print("=" * 70)
        print(
            f"Spiel-ID:              "
            f"{result.match_id}"
        )
        print(
            f"Seitentitel:           "
            f"{result.page_title}"
        )
        print(
            f"Liveticker erkannt:    "
            f"{'JA' if result.ticker_available else 'NEIN'}"
        )
        print(
            f"Ticker-Selektoren:     "
            f"{len(result.ticker_selectors_found)}"
        )
        print(
            f"Ticker-Links:          "
            f"{len(result.ticker_links_found)}"
        )
        print(
            f"Event-Elemente:        "
            f"{result.event_rows_found}"
        )
        print(
            f"Timeline-Events:       "
            f"{result.timeline_events_found}"
        )
        print(
            f"HTML gespeichert:      "
            f"{result.html_path}"
        )
        print(
            f"Bericht gespeichert:   "
            f"{result.report_path}"
        )
        print("=" * 70)

        if result.ticker_links_found:
            print()
            print("GEFUNDENE TICKER-LINKS")
            print("-" * 70)

            for link in result.ticker_links_found:
                print(link)

    @staticmethod
    def _extract_match_id(
        source_url: str,
        soup: BeautifulSoup,
    ) -> str:
        candidates = [
            source_url
        ]

        canonical = soup.select_one(
            "link[rel='canonical']"
        )

        if canonical is not None:
            candidates.append(
                str(
                    canonical.get(
                        "href",
                        "",
                    )
                    or ""
                )
            )

        for candidate in candidates:
            if not candidate:
                continue

            parsed_url = urlparse(
                candidate
            )

            match = re.search(
                r"/-/spiel/([^/#!?]+)",
                parsed_url.path,
                re.IGNORECASE,
            )

            if match:
                return match.group(1)

            match = re.search(
                r"/spiel/([^/#!?]+)$",
                parsed_url.path,
                re.IGNORECASE,
            )

            if match:
                return match.group(1)

        return ""


def main() -> None:
    print(
        "Dieses Modul wird über ein separates "
        "Testskript aufgerufen."
    )


if __name__ == "__main__":
    main()
