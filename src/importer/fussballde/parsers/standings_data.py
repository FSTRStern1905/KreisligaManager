from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.font_decoder import FontDecoder
from src.importer.fussballde.parsers.base_parser import BaseParser
from src.importer.fussballde.parsers.standings_data import (
    StandingRow,
    StandingsData,
)


class StandingsParser(BaseParser):
    """
    Liest die offizielle Tabelle einer Staffel von fussball.de aus.

    Der Parser ist absichtlich tolerant gegenüber leicht unterschiedlichen
    Tabellenaufbauten. Er erkennt die benötigten Werte sowohl über bekannte
    CSS-Klassen als auch über die Reihenfolge numerischer Spalten.
    """

    TABLE_SELECTORS = (
        "#standing-table",
        "#table-standing",
        "table[id*='standing']",
        "table[class*='standing']",
        ".table-standing table",
        ".standing-table table",
        "table:has(th:has-text('Pkt'))",
        "table:has(th:has-text('Punkte'))",
    )

    TEAM_CELL_SELECTORS = (
        "td.column-team",
        "td.column-club",
        "td[class*='team']",
        "td[class*='club']",
        "td:nth-of-type(2)",
    )

    POSITION_PATTERN = re.compile(r"^\s*(\d{1,2})\.?\s*$")
    INTEGER_PATTERN = re.compile(r"-?\d+")
    GOALS_PATTERN = re.compile(r"(\d+)\s*:\s*(\d+)")

    def __init__(self, page: Any) -> None:
        super().__init__(page)
        self.font_decoder = FontDecoder(request_context=page.request)

    def parse(self) -> StandingsData:
        soup = BeautifulSoup(self.page.content(), "lxml")
        table = self._find_table(soup)

        if table is None:
            raise RuntimeError(
                "Die Tabellenansicht von fussball.de wurde nicht gefunden."
            )

        rows: list[StandingRow] = []

        for table_row in table.select("tbody > tr"):
            if not isinstance(table_row, Tag):
                continue

            standing_row = self._parse_row(table_row)

            if standing_row is not None:
                rows.append(standing_row)

        if not rows:
            raise RuntimeError(
                "Die Tabelle wurde gefunden, enthielt aber keine lesbaren "
                "Mannschaftszeilen."
            )

        rows.sort(key=lambda row: row.position)

        print(f"Gefundene Tabellenmannschaften: {len(rows)}")

        return StandingsData(
            competition_name=self._extract_competition_name(soup),
            season_name=self._extract_season_name(soup),
            rows=rows,
        )

    def _find_table(self, soup: BeautifulSoup) -> Tag | None:
        for selector in self.TABLE_SELECTORS:
            candidate = soup.select_one(selector)

            if isinstance(candidate, Tag):
                return candidate

        for candidate in soup.select("table"):
            if not isinstance(candidate, Tag):
                continue

            header_text = self._get_text(candidate.select_one("thead"))
            normalized_header = header_text.casefold()

            has_points = "pkt" in normalized_header or "punkte" in normalized_header
            has_matches = "sp" in normalized_header or "spiele" in normalized_header

            if has_points and has_matches:
                return candidate

        return None

    def _parse_row(self, row: Tag) -> StandingRow | None:
        cells = [cell for cell in row.select("td") if isinstance(cell, Tag)]

        if len(cells) < 6:
            return None

        position = self._extract_position(cells, row)
        team_cell = self._find_team_cell(row, cells)
        team_name = self._extract_team_name(team_cell)

        if position is None or not team_name:
            return None

        team_url = self._extract_team_url(team_cell)
        values = self._extract_stat_values(cells, team_cell)

        if values is None:
            return None

        (
            played,
            wins,
            draws,
            losses,
            goals_for,
            goals_against,
            goal_difference,
            points,
        ) = values

        return StandingRow(
            position=position,
            team_name=team_name,
            played=played,
            wins=wins,
            draws=draws,
            losses=losses,
            goals_for=goals_for,
            goals_against=goals_against,
            goal_difference=goal_difference,
            points=points,
            team_url=team_url,
        )

    def _extract_position(
        self,
        cells: list[Tag],
        row: Tag,
    ) -> int | None:
        position_cell = row.select_one(
            "td.column-rank, td.column-position, td[class*='rank'], "
            "td[class*='position']"
        )

        candidates = [position_cell, cells[0]]

        for candidate in candidates:
            if not isinstance(candidate, Tag):
                continue

            match = self.POSITION_PATTERN.match(self._get_text(candidate))

            if match:
                return int(match.group(1))

        return None

    def _find_team_cell(
        self,
        row: Tag,
        cells: list[Tag],
    ) -> Tag:
        for selector in self.TEAM_CELL_SELECTORS:
            candidate = row.select_one(selector)

            if isinstance(candidate, Tag):
                return candidate

        return cells[1]

    def _extract_team_name(self, cell: Tag) -> str:
        preferred_selectors = (
            "a.team-name",
            "a.club-name",
            "a[href*='/mannschaft/']",
            "a[href*='/verein/']",
            ".team-name",
            ".club-name",
            "span[class*='team']",
            "span[class*='club']",
        )

        for selector in preferred_selectors:
            candidate = cell.select_one(selector)

            if not isinstance(candidate, Tag):
                continue

            text = self._get_text(candidate)

            if text:
                return text

        return self._get_text(cell)

    def _extract_team_url(self, cell: Tag) -> str:
        link = cell.select_one("a[href]")

        if not isinstance(link, Tag):
            return ""

        href = str(link.get("href", "")).strip()

        if not href:
            return ""

        return urljoin(self.page.url, href)

    def _extract_stat_values(
        self,
        cells: list[Tag],
        team_cell: Tag,
    ) -> tuple[int, int, int, int, int, int, int, int] | None:
        texts = [self._get_text(cell) for cell in cells]

        goals_for, goals_against = self._extract_goals(texts)

        numeric_values: list[int] = []

        for cell in cells:
            if cell is team_cell:
                continue

            text = self._get_text(cell)

            if self.POSITION_PATTERN.match(text):
                continue

            if self.GOALS_PATTERN.search(text):
                continue

            if not re.fullmatch(r"\s*-?\d+\s*", text):
                continue

            numeric_values.append(int(text.strip()))

        if goals_for is None or goals_against is None:
            return self._extract_values_without_combined_goals(numeric_values)

        if len(numeric_values) < 6:
            return None

        played, wins, draws, losses = numeric_values[:4]
        points = numeric_values[-1]
        goal_difference = goals_for - goals_against

        return (
            played,
            wins,
            draws,
            losses,
            goals_for,
            goals_against,
            goal_difference,
            points,
        )

    def _extract_goals(
        self,
        texts: list[str],
    ) -> tuple[int | None, int | None]:
        for text in texts:
            match = self.GOALS_PATTERN.search(text)

            if match:
                return int(match.group(1)), int(match.group(2))

        return None, None

    @staticmethod
    def _extract_values_without_combined_goals(
        numeric_values: list[int],
    ) -> tuple[int, int, int, int, int, int, int, int] | None:
        if len(numeric_values) < 8:
            return None

        played, wins, draws, losses = numeric_values[:4]
        goals_for = numeric_values[4]
        goals_against = numeric_values[5]

        if len(numeric_values) >= 9:
            goal_difference = numeric_values[6]
            points = numeric_values[-1]
        else:
            goal_difference = goals_for - goals_against
            points = numeric_values[-1]

        return (
            played,
            wins,
            draws,
            losses,
            goals_for,
            goals_against,
            goal_difference,
            points,
        )

    def _extract_competition_name(self, soup: BeautifulSoup) -> str:
        selectors = (
            "h1",
            ".stage-content h2",
            ".competition-title",
            "[class*='competition'] h2",
        )

        for selector in selectors:
            candidate = soup.select_one(selector)
            text = self._get_text(candidate)

            if text:
                return text

        return ""

    def _extract_season_name(self, soup: BeautifulSoup) -> str:
        page_text = self._get_text(soup)
        match = re.search(r"\b(20\d{2}/\d{2})\b", page_text)

        if match:
            return match.group(1)

        return ""

    def _get_text(self, element: Tag | BeautifulSoup | None) -> str:
        if element is None:
            return ""

        text = element.get_text(" ", strip=True)
        decoded_text = self.font_decoder.decode_text(text)

        return self.clean_text(decoded_text)