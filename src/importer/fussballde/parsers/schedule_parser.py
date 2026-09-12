from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.font_decoder import FontDecoder
from src.importer.fussballde.parsers.base_parser import BaseParser
from src.importer.fussballde.parsers.schedule_data import (
    ScheduleData,
    ScheduleMatch,
)


class ScheduleParser(BaseParser):
    """
    Liest alle Spiele aus einem Staffelspielplan von fussball.de.

    Dynamisch verschlüsselte Texte werden über den FontDecoder
    entschlüsselt.
    """

    TABLE_SELECTORS = (
        "#fixtures-matchplan-table-matches-table",
        "table[id*='fixtures-matchplan']",
        ".fixtures-matchplan-table",
        "table:has(td.column-club)",
    )

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

    FIXTURE_NUMBER_PATTERN = re.compile(
        r"\b(\d{1,4})\b"
    )

    MATCH_ID_PATTERN = re.compile(
        r"/spiel/[^?#]*/([A-Z0-9]{20,})/?(?:[?#]|$)",
        re.IGNORECASE,
    )

    def __init__(self, page: Any) -> None:
        super().__init__(page)

        self.font_decoder = FontDecoder(
            request_context=page.request
        )

    def parse(self) -> ScheduleData:
        html = self.page.content()
        soup = BeautifulSoup(html, "lxml")

        table: Tag | None = None

        for selector in self.TABLE_SELECTORS:
            candidate = soup.select_one(selector)

            if isinstance(candidate, Tag):
                table = candidate
                break

        if not isinstance(table, Tag):
            raise RuntimeError(
                "Die Spielplan-Tabelle wurde nicht gefunden."
            )

        competition = self._extract_competition(soup)
        category = self._extract_category(soup)

        team_count = self._extract_team_count(table)
        matches_per_matchday = team_count // 2

        print(f"Gefundene Mannschaften: {team_count}")
        print(
            "Spiele pro Spieltag: "
            f"{matches_per_matchday}"
        )

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

        self._assign_matchdays(
            matches=unique_matches,
            matches_per_matchday=matches_per_matchday,
        )

        unique_matches.sort(
            key=self._match_sort_key
        )

        print(f"Gefundene Spiele: {len(unique_matches)}")

        loaded_font_ids = (
            self.font_decoder.get_loaded_font_ids()
        )

        if loaded_font_ids:
            print(
                "Verwendete Schriftarten: "
                + ", ".join(loaded_font_ids)
            )

        return ScheduleData(
            league_name=competition,
            competition_name=competition,
            category=category,
            matches=unique_matches,
        )

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

        if away_team.casefold() == "spielfrei":
            return None

        match_url = self._extract_match_url(row)

        if not match_url:
            return None

        match_id = self._extract_match_id(match_url)

        if not match_id:
            return None

        fixture_number = self._extract_fixture_number(
            row
        )

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

        if (
            "föhren" in home_team.casefold()
            and "issel" in away_team.casefold()
        ):
            score_cell = row.select_one(
                "td.column-score"
            )

            print("\n" + "=" * 80)
            print("DEBUG SPIELPLAN: SV Föhren II - TuS Issel")
            print("=" * 80)
            print(f"Datum: {date_value}")
            print(f"Anstoß: {time_value}")
            print(f"Row-Text: {row_text!r}")
            print(f"home_score: {home_score!r}")
            print(f"away_score: {away_score!r}")
            print(f"status: {status!r}")

            if isinstance(score_cell, Tag):
                print(
                    "Score-Text:",
                    repr(self._get_text(score_cell)),
                )
                print(
                    "Score-HTML:",
                    str(score_cell),
                )

                score_left = score_cell.select_one(
                    ".score-left"
                )
                score_right = score_cell.select_one(
                    ".score-right"
                )

                if isinstance(score_left, Tag):
                    print(
                        "score-left Text:",
                        repr(self._get_text(score_left)),
                    )
                    print(
                        "score-left HTML:",
                        str(score_left),
                    )
                else:
                    print("score-left: NICHT GEFUNDEN")

                if isinstance(score_right, Tag):
                    print(
                        "score-right Text:",
                        repr(self._get_text(score_right)),
                    )
                    print(
                        "score-right HTML:",
                        str(score_right),
                    )
                else:
                    print("score-right: NICHT GEFUNDEN")
            else:
                print("td.column-score: NICHT GEFUNDEN")

            print("=" * 80 + "\n")

        return ScheduleMatch(
            match_id=match_id,
            fixture_number=fixture_number,
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

    def _extract_team_count(
        self,
        table: Tag,
    ) -> int:
        team_names: set[str] = set()

        for cell in table.select("td.column-club"):
            if not isinstance(cell, Tag):
                continue

            team_name = self._extract_team_name(cell)

            if not team_name:
                continue

            if team_name.casefold() == "spielfrei":
                continue

            team_names.add(team_name.casefold())

        return len(team_names)

    def _extract_fixture_number(
        self,
        row: Tag,
    ) -> int | None:
        number_cell = row.select_one(
            "td.hidden-small"
        )

        if not isinstance(number_cell, Tag):
            return None

        number_text = self._get_text(number_cell)

        match = self.FIXTURE_NUMBER_PATTERN.search(
            number_text
        )

        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _assign_matchdays(
        matches: list[ScheduleMatch],
        matches_per_matchday: int,
    ) -> None:
        if matches_per_matchday <= 0:
            return

        for match in matches:
            if match.matchday is not None:
                continue

            if match.fixture_number is None:
                continue

            match.matchday = (
                (match.fixture_number - 1)
                // matches_per_matchday
            ) + 1

    @staticmethod
    def _match_sort_key(
        match: ScheduleMatch,
    ) -> tuple[Any, ...]:
        return (
            match.matchday
            if match.matchday is not None
            else 9999,
            match.fixture_number
            if match.fixture_number is not None
            else 999999,
            match.date,
            match.time,
            match.home_team.casefold(),
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

        info_text = cell.select_one(".info-text")

        if isinstance(info_text, Tag):
            text = self._get_text(info_text)

            if text:
                return text

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

        score_parts = self._extract_score_parts(
            score_cell
        )

        if score_parts is not None:
            return score_parts

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
        seen_match_ids: set[str] = set()

        for match in matches:
            match_id = match.match_id.casefold()

            if match_id in seen_match_ids:
                continue

            seen_match_ids.add(match_id)
            unique_matches.append(match)

        return unique_matches


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:\n"
            "python -m "
            "src.importer.fussballde.parsers."
            "schedule_parser "
            "\"SPIELPLAN-URL\""
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