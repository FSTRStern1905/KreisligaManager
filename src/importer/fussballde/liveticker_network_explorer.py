from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Request, Response

from src.importer.fussballde.browser import FussballDeBrowser


@dataclass(slots=True)
class NetworkEntry:
    method: str
    resource_type: str
    request_url: str
    status: int | None = None
    content_type: str = ""
    saved_path: str = ""
    is_candidate: bool = False
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LivetickerNetworkResult:
    source_url: str
    match_id: str
    page_title: str
    html_path: str
    report_path: str
    requests_total: int
    responses_total: int
    responses_saved: int
    candidate_responses: int
    entries: list[NetworkEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "match_id": self.match_id,
            "page_title": self.page_title,
            "html_path": self.html_path,
            "report_path": self.report_path,
            "requests_total": self.requests_total,
            "responses_total": self.responses_total,
            "responses_saved": self.responses_saved,
            "candidate_responses": self.candidate_responses,
            "entries": [entry.to_dict() for entry in self.entries],
        }


class LivetickerNetworkExplorer:
    DEBUG_ROOT = Path("debug/liveticker_network")

    CANDIDATE_KEYWORDS = (
        "liveticker",
        "live-ticker",
        "ticker",
        "event",
        "events",
        "timeline",
        "match",
        "spiel",
        "comment",
        "comments",
        "lineup",
        "aufstellung",
        "score",
        "goal",
        "card",
        "substitution",
    )

    JSON_CONTENT_TYPES = (
        "application/json",
        "application/ld+json",
        "text/json",
    )

    def explore(
        self,
        url: str,
        headless: bool = False,
        wait_after_load_ms: int = 12_000,
    ) -> LivetickerNetworkResult:
        normalized_url = url.strip()

        if not normalized_url:
            raise ValueError("Die Liveticker-URL darf nicht leer sein.")

        browser = FussballDeBrowser()
        requests: list[Request] = []
        entries: list[NetworkEntry] = []
        response_objects: dict[int, Response] = {}

        try:
            browser.start(headless=headless)

            if browser.page is None:
                raise RuntimeError("Playwright-Seite wurde nicht erstellt.")

            page = browser.page
            page.on("request", lambda request: requests.append(request))
            page.on(
                "response",
                lambda response: self._capture_response(
                    response=response,
                    entries=entries,
                    response_objects=response_objects,
                ),
            )

            print("Öffne Liveticker-Seite ...")
            browser.open(
                normalized_url,
                page_type=FussballDeBrowser.PAGE_TYPE_MATCH_DETAIL,
            )

            print("Warte auf nachgeladene Netzwerkdaten ...")
            page.wait_for_timeout(wait_after_load_ms)
            self._click_possible_ticker_tabs(page)
            page.wait_for_timeout(5_000)

            html = browser.html()
            page_title = browser.title().strip()
            match_id = self._extract_match_id(normalized_url) or "unknown_match"

            match_directory = self.DEBUG_ROOT / match_id
            match_directory.mkdir(parents=True, exist_ok=True)

            html_path = match_directory / "page.html"
            html_path.write_text(html, encoding="utf-8")

            self._save_responses(
                entries=entries,
                response_objects=response_objects,
                match_directory=match_directory,
            )

            result = LivetickerNetworkResult(
                source_url=normalized_url,
                match_id=match_id,
                page_title=page_title,
                html_path=str(html_path),
                report_path="",
                requests_total=len(requests),
                responses_total=len(entries),
                responses_saved=sum(bool(entry.saved_path) for entry in entries),
                candidate_responses=sum(entry.is_candidate for entry in entries),
                entries=entries,
            )

            report_path = match_directory / "network_report.json"
            result.report_path = str(report_path)
            report_path.write_text(
                json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            self._print_result(result)
            return result

        finally:
            browser.close()

    def _capture_response(
        self,
        response: Response,
        entries: list[NetworkEntry],
        response_objects: dict[int, Response],
    ) -> None:
        request = response.request
        content_type = (
            response.headers.get("content-type", "")
            .split(";", 1)[0]
            .strip()
            .casefold()
        )
        url = response.url

        entry = NetworkEntry(
            method=request.method,
            resource_type=request.resource_type,
            request_url=url,
            status=response.status,
            content_type=content_type,
            is_candidate=(
                self._is_candidate_url(url)
                or self._is_json_content_type(content_type)
            ),
        )
        entries.append(entry)
        response_objects[id(entry)] = response

    def _save_responses(
        self,
        entries: list[NetworkEntry],
        response_objects: dict[int, Response],
        match_directory: Path,
    ) -> None:
        response_directory = match_directory / "responses"
        response_directory.mkdir(parents=True, exist_ok=True)
        saved_index = 0

        for entry in entries:
            response = response_objects.get(id(entry))
            if response is None:
                continue

            should_save = (
                self._is_json_content_type(entry.content_type)
                or entry.is_candidate
            )
            if not should_save:
                continue

            try:
                body = response.body()
                if not body:
                    continue

                saved_index += 1
                extension = self._choose_extension(entry.content_type, body)
                filename = (
                    f"{saved_index:03d}_"
                    f"{self._safe_name(entry.request_url)}"
                    f"{extension}"
                )
                path = response_directory / filename

                if extension == ".json":
                    self._write_json_body(path=path, body=body)
                else:
                    path.write_bytes(body)

                entry.saved_path = str(path)

            except Exception as error:
                entry.error = str(error)

    @staticmethod
    def _write_json_body(path: Path, body: bytes) -> None:
        decoded = body.decode("utf-8", errors="replace")
        try:
            parsed = json.loads(decoded)
            path.write_text(
                json.dumps(parsed, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except json.JSONDecodeError:
            path.write_text(decoded, encoding="utf-8")

    def _click_possible_ticker_tabs(self, page) -> None:
        selectors = (
            "a:has-text('Liveticker')",
            "button:has-text('Liveticker')",
            "[data-tab*='live' i]",
            "[href*='liveTicker' i]",
            "[href*='liveticker' i]",
        )

        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if locator.count() == 0:
                    continue
                if not locator.is_visible(timeout=1_000):
                    continue

                print(f"Klicke möglichen Liveticker-Tab: {selector}")
                locator.click(timeout=5_000, force=True)
                page.wait_for_timeout(4_000)
                return
            except Exception:
                continue

    def _is_candidate_url(self, url: str) -> bool:
        normalized = url.casefold()
        return any(keyword in normalized for keyword in self.CANDIDATE_KEYWORDS)

    def _is_json_content_type(self, content_type: str) -> bool:
        return any(json_type in content_type for json_type in self.JSON_CONTENT_TYPES)

    @staticmethod
    def _choose_extension(content_type: str, body: bytes) -> str:
        if "json" in content_type:
            return ".json"

        stripped = body.lstrip()
        if stripped.startswith((b"{", b"[")):
            return ".json"
        if "html" in content_type or stripped.startswith(b"<"):
            return ".html"
        return ".bin"

    @staticmethod
    def _safe_name(url: str) -> str:
        parsed = urlparse(url)
        raw_name = parsed.netloc + parsed.path
        if parsed.query:
            raw_name += "_" + parsed.query

        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_name).strip("._")
        if len(safe) > 120:
            safe = safe[-120:]
        return safe or "response"

    @staticmethod
    def _extract_match_id(url: str) -> str:
        match = re.search(r"/-/spiel/([^/#!?]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)

        match = re.search(r"/spiel/([^/#!?]+)/?$", url, re.IGNORECASE)
        if match:
            return match.group(1)

        return ""

    @staticmethod
    def _print_result(result: LivetickerNetworkResult) -> None:
        print()
        print("=" * 78)
        print("FUSSBALL.DE LIVETICKER NETWORK EXPLORER")
        print("=" * 78)
        print(f"Spiel-ID:               {result.match_id}")
        print(f"Seitentitel:            {result.page_title}")
        print(f"Requests gesamt:        {result.requests_total}")
        print(f"Responses gesamt:       {result.responses_total}")
        print(f"Kandidaten:             {result.candidate_responses}")
        print(f"Antworten gespeichert:  {result.responses_saved}")
        print(f"HTML:                   {result.html_path}")
        print(f"Bericht:                {result.report_path}")
        print("=" * 78)

        candidates = [entry for entry in result.entries if entry.is_candidate]
        if candidates:
            print()
            print("VERDÄCHTIGE ENDPOINTS")
            print("-" * 78)
            for entry in candidates:
                print(
                    f"{entry.status} "
                    f"{entry.resource_type:12} "
                    f"{entry.content_type:24} "
                    f"{entry.request_url}"
                )


def main() -> None:
    print(
        "Dieses Modul wird über "
        "test_liveticker_network_explorer.py gestartet."
    )


if __name__ == "__main__":
    main()