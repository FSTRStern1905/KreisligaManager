import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag
from src.importer.fussballde.parsers.match_html_document import (
    MatchHtmlDocument,
)

from src.importer.fussballde.parsers.base_parser import BaseParser
from src.importer.fussballde.parsers.match_detail_data import (
    MatchDetailData,
    MatchEvent,
)


class MatchDetailParser(BaseParser):
    TEAM_HOME = "home"
    TEAM_AWAY = "away"

    EVENT_GOAL = "goal"
    EVENT_SUBSTITUTION = "substitution"
    EVENT_YELLOW_CARD = "yellow_card"
    EVENT_SECOND_YELLOW_CARD = "second_yellow_card"
    EVENT_RED_CARD = "red_card"
    EVENT_PENALTY_MISSED = "penalty_missed"
    EVENT_OWN_GOAL = "own_goal"
    EVENT_UNKNOWN = "unknown"

    def parse(
        self,
        html: str,
        source_url: str = "",
    ) -> MatchDetailData:
        document = MatchHtmlDocument(html)
        soup = document.soup

        data = MatchDetailData()

        data.match_id = self._extract_match_id(source_url, soup)

        home_team, away_team = self._parse_teams(soup)
        data.home_team = home_team
        data.away_team = away_team

        home_goals, away_goals = self._parse_result(soup)
        data.home_goals = home_goals
        data.away_goals = away_goals

        halftime_home, halftime_away = self._parse_halftime_result(soup)
        data.halftime_home = halftime_home
        data.halftime_away = halftime_away

        match_info = self._parse_match_info(soup)
        data.stadium = match_info["stadium"]
        data.referee = match_info["referee"]
        data.attendance = match_info["attendance"]

        data.events = self._parse_events(
            soup=soup,
            home_team=home_team,
            away_team=away_team,
        )

        self._fill_missing_final_result(data)

        return data

    def _parse_teams(self, soup: BeautifulSoup) -> tuple[str, str]:
        selector_pairs = [
            (
                ".team-home .team-name",
                ".team-away .team-name",
            ),
            (
                ".home-team .team-name",
                ".away-team .team-name",
            ),
            (
                ".team-home",
                ".team-away",
            ),
            (
                ".home-team",
                ".away-team",
            ),
            (
                "[data-team-side='home']",
                "[data-team-side='away']",
            ),
        ]

        for home_selector, away_selector in selector_pairs:
            home_element = soup.select_one(home_selector)
            away_element = soup.select_one(away_selector)

            if home_element and away_element:
                home_team = self.clean_text(
                    home_element.get_text(" ", strip=True)
                )
                away_team = self.clean_text(
                    away_element.get_text(" ", strip=True)
                )

                if home_team and away_team:
                    return home_team, away_team

        team_elements = soup.select(
            ".team-name, .team-name-wrapper, .team-name-container"
        )

        team_names: list[str] = []

        for element in team_elements:
            name = self.clean_text(element.get_text(" ", strip=True))

            if name and name not in team_names:
                team_names.append(name)

        if len(team_names) >= 2:
            return team_names[0], team_names[1]

        return "", ""

    def _parse_result(
        self,
        soup: BeautifulSoup,
    ) -> tuple[int | None, int | None]:
        selector_pairs = [
            (
                ".score-home",
                ".score-away",
            ),
            (
                ".result-home",
                ".result-away",
            ),
            (
                ".home-score",
                ".away-score",
            ),
            (
                "[data-score-home]",
                "[data-score-away]",
            ),
        ]

        for home_selector, away_selector in selector_pairs:
            home_element = soup.select_one(home_selector)
            away_element = soup.select_one(away_selector)

            if not home_element or not away_element:
                continue

            home_goals = self._parse_integer_from_element(home_element)
            away_goals = self._parse_integer_from_element(away_element)

            if home_goals is not None and away_goals is not None:
                return home_goals, away_goals

        result_selectors = [
            ".result",
            ".score",
            ".match-result",
            ".stage-result",
            ".game-result",
        ]

        for selector in result_selectors:
            for element in soup.select(selector):
                result = self._extract_score_from_text(
                    element.get_text(" ", strip=True)
                )

                if result != (None, None):
                    return result

        return None, None

    def _parse_halftime_result(
        self,
        soup: BeautifulSoup,
    ) -> tuple[int | None, int | None]:
        selectors = [
            ".halftime-result",
            ".half-time-result",
            ".result-halftime",
            ".score-halftime",
        ]

        for selector in selectors:
            for element in soup.select(selector):
                score = self._extract_score_from_text(
                    element.get_text(" ", strip=True)
                )

                if score != (None, None):
                    return score

        page_text = soup.get_text(" ", strip=True)

        patterns = [
            r"Halbzeit(?:stand)?\s*:?\s*(\d+)\s*[:\-]\s*(\d+)",
            r"\(\s*(\d+)\s*[:\-]\s*(\d+)\s*\)",
        ]

        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)

            if match:
                return int(match.group(1)), int(match.group(2))

        return None, None

    def _parse_match_info(
        self,
        soup: BeautifulSoup,
    ) -> dict[str, str | int | None]:
        result: dict[str, str | int | None] = {
            "stadium": "",
            "referee": "",
            "attendance": None,
        }

        information_texts = self._collect_match_information_texts(soup)

        for text in information_texts:
            normalized = self.clean_text(text)

            stadium = self._extract_labeled_value(
                normalized,
                labels=[
                    "Spielstätte",
                    "Spielort",
                    "Stadion",
                    "Sportplatz",
                ],
            )

            if stadium and not result["stadium"]:
                result["stadium"] = stadium

            referee = self._extract_labeled_value(
                normalized,
                labels=[
                    "Schiedsrichter",
                    "Schiri",
                    "Referee",
                ],
            )

            if referee and not result["referee"]:
                result["referee"] = referee

            attendance = self._extract_attendance(normalized)

            if attendance is not None and result["attendance"] is None:
                result["attendance"] = attendance

        return result

    def _parse_events(
        self,
        soup: BeautifulSoup,
        home_team: str,
        away_team: str,
    ) -> list[MatchEvent]:
        course = soup.select_one("#match_course_body")

        if course is None:
            course = soup

        events: list[MatchEvent] = []

        for event_element in course.select(".row-event"):
            event = self._parse_event(
                event_element=event_element,
                home_team=home_team,
                away_team=away_team,
            )

            if event is not None:
                events.append(event)

        return events

    def _parse_event(
        self,
        event_element: Tag,
        home_team: str,
        away_team: str,
    ) -> MatchEvent | None:
        team_side = self._extract_team_side(event_element)

        if team_side == self.TEAM_HOME:
            team_name = home_team
        elif team_side == self.TEAM_AWAY:
            team_name = away_team
        else:
            team_name = ""

        minute, additional_time = self._extract_minute(event_element)

        if event_element.select_one(".icon-substitute"):
            return self._parse_substitution(
                event_element=event_element,
                team_name=team_name,
                minute=minute,
                additional_time=additional_time,
            )

        if event_element.select_one(".yellow-card"):
            return self._parse_card(
                event_element=event_element,
                team_name=team_name,
                minute=minute,
                additional_time=additional_time,
                event_type=self.EVENT_YELLOW_CARD,
                value="yellow",
            )

        if event_element.select_one(
            ".yellow-red-card, "
            ".second-yellow-card, "
            ".yellow-card-red-card"
        ):
            return self._parse_card(
                event_element=event_element,
                team_name=team_name,
                minute=minute,
                additional_time=additional_time,
                event_type=self.EVENT_SECOND_YELLOW_CARD,
                value="yellow_red",
            )

        if event_element.select_one(".red-card"):
            return self._parse_card(
                event_element=event_element,
                team_name=team_name,
                minute=minute,
                additional_time=additional_time,
                event_type=self.EVENT_RED_CARD,
                value="red",
            )

        if self._is_goal_event(event_element):
            return self._parse_goal(
                event_element=event_element,
                team_name=team_name,
                minute=minute,
                additional_time=additional_time,
            )

        text = self.clean_text(
            event_element.get_text(" ", strip=True)
        )

        if not text:
            return None

        event_type = self._detect_special_event_type(text)

        player, player_id = self._extract_primary_player(event_element)

        return MatchEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=event_type,
            team=team_name,
            player=player,
            player_id=player_id,
            description=text,
        )

    def _parse_goal(
        self,
        event_element: Tag,
        team_name: str,
        minute: int | None,
        additional_time: int,
    ) -> MatchEvent:
        player, player_id = self._extract_primary_player(event_element)
        home_goals, away_goals = self._extract_event_score(event_element)

        description = self.clean_text(
            event_element.get_text(" ", strip=True)
        )

        event_type = self.EVENT_GOAL
        value = "goal"

        lowered = description.lower()

        if "eigentor" in lowered:
            event_type = self.EVENT_OWN_GOAL
            value = "own_goal"
        elif (
            "elfmeter verschossen" in lowered
            or "foulelfmeter verschossen" in lowered
            or "strafstoß verschossen" in lowered
        ):
            event_type = self.EVENT_PENALTY_MISSED
            value = "penalty_missed"
        elif (
            "elfmeter" in lowered
            or "foulelfmeter" in lowered
            or "strafstoß" in lowered
        ):
            value = "penalty_goal"

        return MatchEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=event_type,
            team=team_name,
            player=player,
            player_id=player_id,
            home_goals=home_goals,
            away_goals=away_goals,
            value=value,
            description=description,
        )

    def _parse_substitution(
        self,
        event_element: Tag,
        team_name: str,
        minute: int | None,
        additional_time: int,
    ) -> MatchEvent:
        player_links = event_element.select(
            ".column-player a[href*='/spielerprofil/']"
        )

        player_in = ""
        player_in_id = ""
        player_out = ""
        player_out_id = ""

        if len(player_links) >= 1:
            player_in = self._extract_player_name(player_links[0])
            player_in_id = self._extract_player_id(player_links[0])

        if len(player_links) >= 2:
            player_out = self._extract_player_name(player_links[1])
            player_out_id = self._extract_player_id(player_links[1])

        description = self.clean_text(
            event_element.get_text(" ", strip=True)
        )

        return MatchEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=self.EVENT_SUBSTITUTION,
            team=team_name,
            player=player_in,
            player_id=player_in_id,
            player_out=player_out,
            player_out_id=player_out_id,
            value="substitution",
            description=description,
        )

    def _parse_card(
        self,
        event_element: Tag,
        team_name: str,
        minute: int | None,
        additional_time: int,
        event_type: str,
        value: str,
    ) -> MatchEvent:
        player, player_id = self._extract_primary_player(event_element)

        description = self.clean_text(
            event_element.get_text(" ", strip=True)
        )

        return MatchEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=event_type,
            team=team_name,
            player=player,
            player_id=player_id,
            value=value,
            description=description,
        )

    def _extract_primary_player(
        self,
        event_element: Tag,
    ) -> tuple[str, str]:
        player_link = event_element.select_one(
            ".column-player a[href*='/spielerprofil/']"
        )

        if player_link is None:
            return "", ""

        return (
            self._extract_player_name(player_link),
            self._extract_player_id(player_link),
        )

    def _extract_player_name(self, player_element: Tag) -> str:
        player_name_element = player_element.select_one(".player-name")

        if player_name_element is None:
            player_name_element = player_element

        player_name = self.clean_text(
            player_name_element.get_text(" ", strip=True)
        )

        if self._contains_private_unicode(player_name):
            return ""

        return player_name

    @staticmethod
    def _extract_player_id(player_element: Tag) -> str:
        href = player_element.get("href", "")

        patterns = [
            r"/player-id/([^/?#!]+)",
            r"/userid/([^/?#!]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, href)

            if match:
                return match.group(1)

        return ""

    def _extract_event_score(
        self,
        event_element: Tag,
    ) -> tuple[int | None, int | None]:
        score_left = event_element.select_one(".score-left")
        score_right = event_element.select_one(".score-right")

        if score_left and score_right:
            home_goals = self._parse_integer_from_element(score_left)
            away_goals = self._parse_integer_from_element(score_right)

            if home_goals is not None and away_goals is not None:
                return home_goals, away_goals

        score_container = event_element.select_one(
            ".column-event .even, .column-event .score"
        )

        if score_container:
            return self._extract_score_from_text(
                score_container.get_text(" ", strip=True)
            )

        return None, None

    @staticmethod
    def _extract_team_side(event_element: Tag) -> str:
        classes = event_element.get("class", [])

        if "event-left" in classes:
            return MatchDetailParser.TEAM_HOME

        if "event-right" in classes:
            return MatchDetailParser.TEAM_AWAY

        return ""

    def _extract_minute(
        self,
        event_element: Tag,
    ) -> tuple[int | None, int]:
        time_element = event_element.select_one(
            ".column-time .valign-inner"
        )

        if time_element is None:
            time_element = event_element.select_one(".column-time")

        if time_element is None:
            return None, 0

        text = self.clean_text(
            time_element.get_text(" ", strip=True)
        )

        match = re.search(
            r"(\d+)(?:\s*\+\s*(\d+))?",
            text,
        )

        if not match:
            return None, 0

        minute = int(match.group(1))
        additional_time = (
            int(match.group(2))
            if match.group(2)
            else 0
        )

        return minute, additional_time

    def _is_goal_event(self, event_element: Tag) -> bool:
        if event_element.select_one(".score-left, .score-right"):
            return True

        if event_element.select_one(
            ".goal, .icon-goal, .icon-ball, .hexagon.green"
        ):
            return True

        text = self.clean_text(
            event_element.get_text(" ", strip=True)
        ).lower()

        return any(
            keyword in text
            for keyword in [
                "tor",
                "eigentor",
                "elfmetertor",
                "foulelfmeter",
                "strafstoß",
            ]
        )

    def _detect_special_event_type(self, text: str) -> str:
        lowered = text.lower()

        if "eigentor" in lowered:
            return self.EVENT_OWN_GOAL

        if (
            "elfmeter verschossen" in lowered
            or "foulelfmeter verschossen" in lowered
            or "strafstoß verschossen" in lowered
        ):
            return self.EVENT_PENALTY_MISSED

        if "gelb-rote karte" in lowered:
            return self.EVENT_SECOND_YELLOW_CARD

        if "rote karte" in lowered:
            return self.EVENT_RED_CARD

        if "gelbe karte" in lowered:
            return self.EVENT_YELLOW_CARD

        if "auswechslung" in lowered:
            return self.EVENT_SUBSTITUTION

        return self.EVENT_UNKNOWN

    def _collect_match_information_texts(
        self,
        soup: BeautifulSoup,
    ) -> list[str]:
        selectors = [
            ".stage",
            ".stage-content",
            ".match-stage",
            ".match-info",
            ".game-info",
            ".location",
            ".referee",
            ".attendance",
        ]

        texts: list[str] = []

        for selector in selectors:
            for element in soup.select(selector):
                text = self.clean_text(
                    element.get_text(" ", strip=True)
                )

                if text and text not in texts:
                    texts.append(text)

        if not texts:
            texts.append(
                self.clean_text(soup.get_text(" ", strip=True))
            )

        return texts

    @staticmethod
    def _extract_labeled_value(
        text: str,
        labels: list[str],
    ) -> str:
        for label in labels:
            pattern = (
                rf"{re.escape(label)}\s*:?\s*"
                rf"(.+?)"
                rf"(?=\s+(?:"
                rf"Schiedsrichter|Schiri|Referee|"
                rf"Zuschauer|Spielstätte|Spielort|"
                rf"Stadion|Sportplatz"
                rf")\s*:|$)"
            )

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return match.group(1).strip(" -|")

        return ""

    @staticmethod
    def _extract_attendance(text: str) -> int | None:
        patterns = [
            r"Zuschauer\s*:?\s*([\d.]+)",
            r"Besucher\s*:?\s*([\d.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                value = match.group(1).replace(".", "")

                if value.isdigit():
                    return int(value)

        return None

    def _extract_score_from_text(
        self,
        text: str,
    ) -> tuple[int | None, int | None]:
        cleaned = self.clean_text(text)

        match = re.search(
            r"(?<!\d)(\d+)\s*[:\-]\s*(\d+)(?!\d)",
            cleaned,
        )

        if not match:
            return None, None

        return int(match.group(1)), int(match.group(2))

    def _parse_integer_from_element(
        self,
        element: Tag,
    ) -> int | None:
        attributes = [
            "data-score-home",
            "data-score-away",
            "data-value",
            "content",
        ]

        for attribute in attributes:
            value = element.get(attribute)

            if value is not None:
                parsed = self._parse_integer(str(value))

                if parsed is not None:
                    return parsed

        text = self.clean_text(element.get_text(" ", strip=True))

        return self._parse_integer(text)

    @staticmethod
    def _parse_integer(value: str) -> int | None:
        match = re.search(r"\d+", value)

        if not match:
            return None

        return int(match.group())

    @staticmethod
    def _contains_private_unicode(value: str) -> bool:
        return any(
            0xE000 <= ord(character) <= 0xF8FF
            for character in value
        )

    @staticmethod
    def _extract_match_id(
        source_url: str,
        soup: BeautifulSoup,
    ) -> str:
        candidates = [source_url]

        canonical = soup.select_one("link[rel='canonical']")

        if canonical:
            candidates.append(canonical.get("href", ""))

        for candidate in candidates:
            if not candidate:
                continue

            parsed_url = urlparse(candidate)
            path = parsed_url.path

            match = re.search(
                r"/spiel/([^/]+)/?$",
                path,
                re.IGNORECASE,
            )

            if match:
                return match.group(1)

            match = re.search(
                r"/spiel/[^/]+/[^/]+/-/spiel/([^/#!?]+)",
                candidate,
                re.IGNORECASE,
            )

            if match:
                return match.group(1)

            match = re.search(
                r"/-/spiel/([^/#!?]+)",
                candidate,
                re.IGNORECASE,
            )

            if match:
                return match.group(1)

        return ""

    @staticmethod
    def _fill_missing_final_result(
        data: MatchDetailData,
    ) -> None:
        if (
            data.home_goals is not None
            and data.away_goals is not None
        ):
            return

        goal_events = [
            event
            for event in data.events
            if (
                event.home_goals is not None
                and event.away_goals is not None
            )
        ]

        if not goal_events:
            return

        final_event = goal_events[-1]

        data.home_goals = final_event.home_goals
        data.away_goals = final_event.away_goals