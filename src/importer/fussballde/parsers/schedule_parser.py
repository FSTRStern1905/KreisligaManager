from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.font_decoder import FontDecoder
from src.importer.fussballde.parsers.base_parser import BaseParser


@dataclass
class ScheduleMatch:
    match_id: str
    matchday: int | None
    date: str
    time: str
    competition: str
    category: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: str
    match_url: str


class ScheduleParser(BaseParser):
    """
    Liest alle Spiele aus dem Staffelspielplan von fussball.de.

    Playwright lädt die vollständige JavaScript-Seite.
    BeautifulSoup verarbeitet anschließend die Spielzeilen.
    Dynamische fussball.de-Schriftarten werden automatisch entschlüsselt.
    """

    TABLE_SELECTOR = "#fixtures-matchplan-table-matches-table"

    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}\.\d{1,2}\.(?:\d{2}|\d{4}))\b"
    )

    TIME_PATTERN = re.compile(
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b"
    )

    SCORE_PATTERN = re.compile(
        r"(?<!\d)(\d{1,2})\s*:\s*(\d{1,2})(?!\d)"
    )

    MATCHDAY_PATTERN = re.compile(
        r"\b(\d{1,2})\.\s*Spieltag\b",
        re.IGNORECASE,
    )

    MATCH_ID_PATTERN = re.compile(
        r"/spiel/[^?#]*/([A-Z0-9]{20,})/?(?:[?#]|$)",
        re.IGNORECASE,
    )

    FONT_CLASS_PATTERN = re.compile(
        r"(?:^|\s)results-c-([a-zA-Z0-9]+)(?:\s|$)"
    )

    def __init__(self, page: Any) -> None:
        super().__init__(page)

        self.font_decoder = FontDecoder(
            request_context=page.request
        )

    def parse(self) -> list[ScheduleMatch]:
        html = self.page.content()
        soup = BeautifulSoup(html, "lxml")

        table = soup.select_one(self.TABLE_SELECTOR)

        if not isinstance(table, Tag):
            raise RuntimeError(
                "Die Spielplan-Tabelle wurde nicht gefunden."
            )

        competition = self._extract_competition(soup)
        category = self._extract_category(soup)

        matches: list[ScheduleMatch] = []
        current_matchday: int | None = None
        current_date = ""

        rows = table.select("tbody > tr")

        print(f"Gefundene Tabellenzeilen: {len(rows)}")

        for row in rows:
            if not isinstance(row, Tag):
                continue

            if self._is_headline_row(row):
                headline_text = self._get_text(row)

                extracted_matchday = self._extract_matchday(
                    headline_text
                )

                extracted_date = self._extract_date(
                    headline_text
                )

                if extracted_matchday is not None:
                    current_matchday = extracted_matchday

                if extracted_date:
                    current_date = extracted_date

                continue

            match = self._parse_match_row(
                row=row,
                competition=competition,
                category=category,
                fallback_matchday=current_matchday,
                fallback_date=current_date,
            )

            if match is not None:
                matches.append(match)

        unique_matches = self._remove_duplicates(matches)

        print(f"Gefundene Spiele: {len(unique_matches)}")

        loaded_font_ids = (
            self.font_decoder.get_loaded_font_ids()
        )

        if loaded_font_ids:
            print(
                "Verwendete Schriftarten: "
                + ", ".join(loaded_font_ids)
            )

        return unique_matches

    def _parse_match_row(
        self,
        row: Tag,
        competition: str,
        category: str,
        fallback_matchday: int | None,
        fallback_date: str,
    ) -> ScheduleMatch | None:
        team_cells = row.select("td.column-club")

        if len(team_cells) < 2:
            return None

        home_team = self._extract_team_name(
            team_cells[0]
        )

        away_team = self._extract_team_name(
            team_cells[1]
        )

        if not home_team or not away_team:
            return None

        match_url = self._extract_match_url(row)

        if not match_url:
            return None

        match_id = self._extract_match_id(match_url)

        if not match_id:
            return None

        row_text = self._get_text(row)

        date_cell = row.select_one("td.column-date")
        date_text = self._get_text(date_cell)

        date_value = (
            self._extract_date(date_text)
            or self._extract_date(row_text)
            or fallback_date
        )

        time_value = (
            self._extract_time(date_text)
            or self._extract_time(row_text)
        )

        matchday = (
            self._extract_matchday(row_text)
            or fallback_matchday
        )

        home_score, away_score = self._extract_score(
            row=row,
            time_value=time_value,
        )

        status = self._extract_status(
            row_text=row_text,
            home_score=home_score,
            away_score=away_score,
        )

        return ScheduleMatch(
            match_id=match_id,
            matchday=matchday,
            date=date_value,
            time=time_value,
            competition=competition,
            category=category,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            status=status,
            match_url=match_url,
        )

    @staticmethod
    def _is_headline_row(row: Tag) -> bool:
        classes = row.get("class", [])

        return "row-headline" in classes

    def _extract_team_name(self, cell: Tag) -> str:
        club_name = cell.select_one(".club-name")

        if isinstance(club_name, Tag):
            team_name = self._get_text(club_name)

            if team_name:
                return team_name

        logo = cell.select_one("img[alt]")

        if isinstance(logo, Tag):
            alt_text = self.clean_text(
                str(logo.get("alt", ""))
            )

            if alt_text:
                return alt_text

        club_link = cell.select_one("a.club-wrapper")

        if isinstance(club_link, Tag):
            return self._get_text(club_link)

        return ""

    def _extract_match_url(self, row: Tag) -> str:
        selectors = (
            "td.column-detail a[href*='/spiel/']",
            "td.column-score a[href*='/spiel/']",
            "a[href*='/spiel/']",
        )

        for selector in selectors:
            link = row.select_one(selector)

            if not isinstance(link, Tag):
                continue

            href = self.clean_text(
                str(link.get("href", ""))
            )

            if href:
                return self._normalize_url(href)

        return ""

    def _extract_score(
        self,
        row: Tag,
        time_value: str,
    ) -> tuple[int | None, int | None]:
        score_cell = row.select_one("td.column-score")

        if not isinstance(score_cell, Tag):
            return None, None

        possible_values: list[str] = []

        for attribute_name in (
            "data-result",
            "data-score",
            "aria-label",
            "title",
        ):
            value = score_cell.get(attribute_name)

            if value:
                possible_values.append(
                    self.clean_text(str(value))
                )

        for element in score_cell.select(
            "[data-result], "
            "[data-score], "
            "[aria-label], "
            "[title]"
        ):
            if not isinstance(element, Tag):
                continue

            for attribute_name in (
                "data-result",
                "data-score",
                "aria-label",
                "title",
            ):
                value = element.get(attribute_name)

                if value:
                    possible_values.append(
                        self.clean_text(str(value))
                    )

        possible_values.append(
            self._get_text(score_cell)
        )

        score_parts = self._extract_score_parts(
            score_cell
        )

        if score_parts is not None:
            return score_parts

        for value in possible_values:
            for score_match in self.SCORE_PATTERN.finditer(
                value
            ):
                score_text = score_match.group(0)

                if (
                    time_value
                    and score_text == time_value
                ):
                    continue

                return (
                    int(score_match.group(1)),
                    int(score_match.group(2)),
                )

        return None, None

    def _extract_score_parts(
        self,
        score_cell: Tag,
    ) -> tuple[int, int] | None:
        score_left = score_cell.select_one(
            ".score-left"
        )

        score_right = score_cell.select_one(
            ".score-right"
        )

        if not isinstance(score_left, Tag):
            return None

        if not isinstance(score_right, Tag):
            return None

        home_text = self._get_text(score_left)
        away_text = self._get_text(score_right)

        if not home_text.isdigit():
            return None

        if not away_text.isdigit():
            return None

        return int(home_text), int(away_text)

    def _extract_status(
        self,
        row_text: str,
        home_score: int | None,
        away_score: int | None,
    ) -> str:
        normalized = row_text.casefold()

        status_keywords = {
            "abgesetzt": "cancelled",
            "abgebrochen": "abandoned",
            "annulliert": "cancelled",
            "ausgefallen": "cancelled",
            "nichtantritt": "walkover",
            "nicht angetreten": "walkover",
            "verlegt": "postponed",
            "verschoben": "postponed",
            "wertung": "awarded",
            "beendet": "finished",
            "endstand": "finished",
            "live": "live",
        }

        for keyword, status in status_keywords.items():
            if keyword in normalized:
                return status

        if (
            home_score is not None
            and away_score is not None
        ):
            return "finished"

        return "scheduled"

    def _extract_competition(
        self,
        soup: BeautifulSoup,
    ) -> str:
        selectors = (
            "#stage h2",
            ".stage-content h2",
            "[data-competition]",
        )

        for selector in selectors:
            element = soup.select_one(selector)

            if not isinstance(element, Tag):
                continue

            data_value = element.get(
                "data-competition"
            )

            if data_value:
                return self.clean_text(
                    str(data_value)
                )

            text = self._get_text(element)

            if text:
                return text

        return ""

    def _extract_category(
        self,
        soup: BeautifulSoup,
    ) -> str:
        selectors = (
            "[data-category]",
            ".category",
            ".age-group",
            ".game-type",
        )

        for selector in selectors:
            element = soup.select_one(selector)

            if not isinstance(element, Tag):
                continue

            data_value = element.get(
                "data-category"
            )

            if data_value:
                return self.clean_text(
                    str(data_value)
                )

            text = self._get_text(element)

            if text:
                return text

        return ""

    def _normalize_url(self, href: str) -> str:
        absolute_url = urljoin(
            self.page.url,
            href,
        )

        parsed_url = urlparse(absolute_url)

        return parsed_url._replace(
            fragment=""
        ).geturl()

    def _extract_match_id(
        self,
        match_url: str,
    ) -> str:
        match = self.MATCH_ID_PATTERN.search(
            match_url
        )

        if match:
            return match.group(1).upper()

        path_parts = [
            part
            for part in urlparse(
                match_url
            ).path.split("/")
            if part
        ]

        for part in reversed(path_parts):
            if len(part) < 20:
                continue

            if re.fullmatch(
                r"[A-Za-z0-9]+",
                part,
            ):
                return part.upper()

        return ""

    def _extract_date(self, value: str) -> str:
        match = self.DATE_PATTERN.search(value)

        if not match:
            return ""

        raw_date = match.group(1)

        for date_format in (
            "%d.%m.%Y",
            "%d.%m.%y",
        ):
            try:
                parsed_date = datetime.strptime(
                    raw_date,
                    date_format,
                )

                return parsed_date.date().isoformat()

            except ValueError:
                continue

        return ""

    def _extract_time(self, value: str) -> str:
        match = self.TIME_PATTERN.search(value)

        if not match:
            return ""

        return match.group(0)

    def _extract_matchday(
        self,
        value: str,
    ) -> int | None:
        match = self.MATCHDAY_PATTERN.search(value)

        if not match:
            return None

        return int(match.group(1))

    def _get_text(
        self,
        element: Tag | None,
    ) -> str:
        if not isinstance(element, Tag):
            return ""

        text_parts: list[str] = []

        for descendant in element.descendants:
            if not isinstance(
                descendant,
                NavigableString,
            ):
                continue

            raw_text = str(descendant)

            if not raw_text:
                continue

            decoded_text = self._decode_text_node(
                text_node=descendant,
                root_element=element,
            )

            text_parts.append(decoded_text)

        return self.clean_text(
            " ".join(text_parts)
        )

    def _decode_text_node(
        self,
        text_node: NavigableString,
        root_element: Tag,
    ) -> str:
        text = str(text_node)

        current_parent = text_node.parent

        while isinstance(current_parent, Tag):
            class_name = self._get_class_name(
                current_parent
            )

            font_id = (
                self.font_decoder.extract_font_id(
                    class_name
                )
            )

            if font_id:
                try:
                    return self.font_decoder.decode(
                        text=text,
                        font_id=font_id,
                    )
                except Exception as error:
                    print(
                        "Warnung: Text konnte nicht "
                        "entschlüsselt werden: "
                        f"{error}"
                    )

                    return text

            if current_parent is root_element:
                break

            current_parent = current_parent.parent

        return text

    @staticmethod
    def _get_class_name(
        element: Tag,
    ) -> str:
        classes = element.get("class", [])

        if isinstance(classes, str):
            return classes

        if isinstance(classes, list):
            return " ".join(
                str(class_name)
                for class_name in classes
            )

        return ""

    @staticmethod
    def _remove_duplicates(
        matches: list[ScheduleMatch],
    ) -> list[ScheduleMatch]:
        unique_matches: list[ScheduleMatch] = []
        seen: set[tuple[Any, ...]] = set()

        for match in matches:
            key = (
                match.match_id.casefold(),
                match.match_url.casefold(),
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
            "python -m "
            "src.importer.fussballde.parsers."
            "schedule_parser "
            "\"https://www.fussball.de/"
            "spielplan/.../section/matchplan\""
        )

        sys.exit(1)

    url = sys.argv[1]
    browser = FussballDeBrowser()

    try:
        print("Browser wird gestartet ...")
        browser.start()

        print("Matchplan wird geladen ...")
        browser.open(url)

        if browser.page is None:
            raise RuntimeError(
                "Die fussball.de-Seite wurde "
                "nicht geladen."
            )

        print("HTML wird verarbeitet ...")

        parser = ScheduleParser(browser.page)
        matches = parser.parse()

        print(
            json.dumps(
                [
                    asdict(match)
                    for match in matches
                ],
                ensure_ascii=False,
                indent=2,
            )
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()