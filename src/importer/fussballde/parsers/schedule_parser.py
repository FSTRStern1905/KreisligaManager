import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from playwright.sync_api import Locator

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.parsers.base_parser import BaseParser


@dataclass
class ScheduleMatch:
    date: str
    time: str
    competition: str
    category: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    match_url: str


class ScheduleParser(BaseParser):
    """
    Liest den sichtbaren Spielplan einer fussball.de-Mannschaftsseite aus.
    """

    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}\.\d{1,2}\.(?:\d{2}|\d{4}))\b"
    )

    TIME_PATTERN = re.compile(
        r"\b([01]?\d|2[0-3]):[0-5]\d\b"
    )

    SCORE_PATTERN = re.compile(
        r"\b(\d{1,2})\s*:\s*(\d{1,2})\b"
    )

    def parse(self) -> list[ScheduleMatch]:
        matches: list[ScheduleMatch] = []
        current_date = ""

        tables = self.page.locator("table")

        for table_index in range(tables.count()):
            table = tables.nth(table_index)

            try:
                if not table.is_visible():
                    continue
            except Exception:
                continue

            rows = table.locator("tr")

            for row_index in range(rows.count()):
                row = rows.nth(row_index)
                cells = self._read_cells(row)

                if not cells:
                    continue

                row_text = self.clean_text(" | ".join(cells))

                date_from_row = self._extract_date(row_text)

                if self._is_date_header(cells, row_text):
                    if date_from_row:
                        current_date = date_from_row

                    continue

                parsed_match = self._parse_match_row(
                    row=row,
                    cells=cells,
                    fallback_date=current_date,
                )

                if parsed_match is not None:
                    matches.append(parsed_match)

        return self._remove_duplicates(matches)

    def _parse_match_row(
        self,
        row: Locator,
        cells: list[str],
        fallback_date: str,
    ) -> ScheduleMatch | None:
        row_text = self.clean_text(" | ".join(cells))

        time_value = self._extract_time(row_text)

        if not time_value:
            return None

        date_value = self._extract_date(row_text) or fallback_date

        if not date_value:
            return None

        time_cell_index = self._find_time_cell_index(cells)

        if time_cell_index is None:
            return None

        competition = self._value_at(cells, time_cell_index + 1)
        category = self._value_at(cells, time_cell_index + 2)
        home_team = self._value_at(cells, time_cell_index + 3)

        separator_index = self._find_team_separator_index(
            cells=cells,
            start_index=time_cell_index + 4,
        )

        if separator_index is None:
            return None

        away_team = self._value_at(cells, separator_index + 1)

        if not home_team or not away_team:
            return None

        home_score, away_score = self._extract_score(row, cells)
        match_url = self._extract_match_url(row)

        return ScheduleMatch(
            date=date_value,
            time=time_value,
            competition=competition,
            category=category,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            match_url=match_url,
        )

    def _read_cells(self, row: Locator) -> list[str]:
        values: list[str] = []
        cells = row.locator("th, td")

        for cell_index in range(cells.count()):
            cell = cells.nth(cell_index)

            try:
                value = self.clean_text(cell.inner_text(timeout=1_000))
            except Exception:
                value = ""

            values.append(value)

        return values

    def _extract_score(
        self,
        row: Locator,
        cells: list[str],
    ) -> tuple[int | None, int | None]:
        possible_values: list[str] = list(cells)

        score_elements = row.locator(
            "[data-result], "
            "[data-score], "
            "[aria-label], "
            "[title], "
            ".score, "
            ".result, "
            ".比分"
        )

        for element_index in range(score_elements.count()):
            element = score_elements.nth(element_index)

            for attribute_name in (
                "data-result",
                "data-score",
                "aria-label",
                "title",
            ):
                try:
                    attribute_value = element.get_attribute(
                        attribute_name,
                        timeout=500,
                    )
                except Exception:
                    attribute_value = None

                if attribute_value:
                    possible_values.append(attribute_value)

            try:
                element_text = self.clean_text(
                    element.inner_text(timeout=500)
                )
            except Exception:
                element_text = ""

            if element_text:
                possible_values.append(element_text)

        for value in possible_values:
            score_match = self.SCORE_PATTERN.search(value)

            if not score_match:
                continue

            return (
                int(score_match.group(1)),
                int(score_match.group(2)),
            )

        return None, None

    def _extract_match_url(self, row: Locator) -> str:
        links = row.locator("a[href]")

        fallback_url = ""

        for link_index in range(links.count()):
            link = links.nth(link_index)

            try:
                href = link.get_attribute("href", timeout=1_000) or ""
                text = self.clean_text(link.inner_text(timeout=1_000))
            except Exception:
                continue

            if not href:
                continue

            absolute_url = urljoin(self.page.url, href)

            if not fallback_url:
                fallback_url = absolute_url

            normalized_text = text.lower()
            normalized_href = href.lower()

            if (
                "zum spiel" in normalized_text
                or "/spiel/" in normalized_href
                or "spielbericht" in normalized_href
            ):
                return absolute_url

        return fallback_url

    def _extract_date(self, value: str) -> str:
        match = self.DATE_PATTERN.search(value)

        if not match:
            return ""

        raw_date = match.group(1)

        for date_format in ("%d.%m.%Y", "%d.%m.%y"):
            try:
                parsed_date = datetime.strptime(raw_date, date_format)
                return parsed_date.date().isoformat()
            except ValueError:
                continue

        return ""

    def _extract_time(self, value: str) -> str:
        match = self.TIME_PATTERN.search(value)

        if not match:
            return ""

        return match.group(0)

    def _find_time_cell_index(
        self,
        cells: list[str],
    ) -> int | None:
        for index, value in enumerate(cells):
            if self.TIME_PATTERN.search(value):
                return index

        return None

    @staticmethod
    def _find_team_separator_index(
        cells: list[str],
        start_index: int,
    ) -> int | None:
        for index in range(start_index, len(cells)):
            value = BaseParser.clean_text(cells[index])

            if value in {":", "-", "–", "—"}:
                return index

        return None

    def _is_date_header(
        self,
        cells: list[str],
        row_text: str,
    ) -> bool:
        if not self._extract_date(row_text):
            return False

        if self._extract_time(row_text):
            return False

        non_empty_cells = [
            value
            for value in cells
            if self.clean_text(value)
        ]

        return len(non_empty_cells) <= 2

    @staticmethod
    def _value_at(
        values: list[str],
        index: int,
    ) -> str:
        if index < 0 or index >= len(values):
            return ""

        return BaseParser.clean_text(values[index])

    @staticmethod
    def _remove_duplicates(
        matches: list[ScheduleMatch],
    ) -> list[ScheduleMatch]:
        unique_matches: list[ScheduleMatch] = []
        seen: set[tuple[Any, ...]] = set()

        for match in matches:
            key = (
                match.date,
                match.time,
                match.home_team.lower(),
                match.away_team.lower(),
                match.match_url,
            )

            if key in seen:
                continue

            seen.add(key)
            unique_matches.append(match)

        return unique_matches


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m src.importer.fussballde.parsers.schedule_parser "
            "\"https://www.fussball.de/...\""
        )
        sys.exit(1)

    url = sys.argv[1]
    browser = FussballDeBrowser()

    try:
        browser.start()
        browser.open(url)

        if browser.page is None:
            raise RuntimeError("Die fussball.de-Seite wurde nicht geladen.")

        parser = ScheduleParser(browser.page)
        matches = parser.parse()

        print(f"\nGefundene Spiele: {len(matches)}\n")

        print(
            json.dumps(
                [asdict(match) for match in matches],
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        browser.close()


if __name__ == "__main__":
    main()