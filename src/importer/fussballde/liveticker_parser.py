from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.liveticker_data import (
    LivetickerData,
    LivetickerEvent,
)


class LivetickerParser:
    EVENT_TYPE_UNKNOWN = "unknown"
    EVENT_TYPE_GOAL = "goal"
    EVENT_TYPE_OWN_GOAL = "own_goal"
    EVENT_TYPE_PENALTY_GOAL = "penalty_goal"
    EVENT_TYPE_PENALTY_MISSED = "penalty_missed"
    EVENT_TYPE_YELLOW_CARD = "yellow_card"
    EVENT_TYPE_YELLOW_RED_CARD = "yellow_red_card"
    EVENT_TYPE_RED_CARD = "red_card"
    EVENT_TYPE_SUBSTITUTION = "substitution"
    EVENT_TYPE_KICKOFF = "kickoff"
    EVENT_TYPE_HALFTIME = "halftime"
    EVENT_TYPE_FULLTIME = "fulltime"
    EVENT_TYPE_COMMENT = "comment"

    HTML_EVENT_SELECTORS = (
        ".liveticker-event",
        ".live-ticker-event",
        ".ticker-event",
        "[class*='liveticker-event']",
        "[class*='live-ticker-event']",
        "[class*='ticker-event']",
        "[data-event-type]",
    )

    def parse_html(
        self,
        html: str,
        source_url: str = "",
        match_id: str = "",
    ) -> LivetickerData:
        if not html.strip():
            raise ValueError(
                "Das HTML darf nicht leer sein."
            )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        data = LivetickerData(
            source_url=source_url,
            match_id=match_id,
            page_title=self._extract_page_title(
                soup
            ),
            ticker_available=False,
            source_type="html",
        )

        data.home_team, data.away_team = (
            self._extract_teams_from_html(
                soup
            )
        )

        (
            data.home_score,
            data.away_score,
        ) = self._extract_score_from_html(
            soup
        )

        event_elements = (
            self._collect_html_event_elements(
                soup
            )
        )

        for event_element in event_elements:
            event = self._parse_html_event(
                event_element
            )

            if event is not None:
                data.events.append(
                    event
                )

        data.ticker_available = bool(
            data.events
            or self._has_ticker_container(
                soup
            )
        )

        if not data.ticker_available:
            data.warnings.append(
                "Kein eindeutiger Liveticker "
                "im HTML erkannt."
            )

        return data

    def parse_json(
        self,
        payload: str | dict | list,
        source_url: str = "",
        match_id: str = "",
    ) -> LivetickerData:
        parsed_payload = self._normalize_json_payload(
            payload
        )

        data = LivetickerData(
            source_url=source_url,
            match_id=match_id,
            ticker_available=True,
            source_type="json",
        )

        root = self._extract_json_root(
            parsed_payload
        )

        data.page_title = self._get_first_text(
            root,
            (
                "title",
                "pageTitle",
                "matchTitle",
                "name",
            ),
        )

        data.competition = self._get_first_text(
            root,
            (
                "competition",
                "competitionName",
                "league",
                "leagueName",
            ),
        )

        data.home_team = self._extract_json_team(
            root,
            side="home",
        )
        data.away_team = self._extract_json_team(
            root,
            side="away",
        )

        (
            data.home_score,
            data.away_score,
        ) = self._extract_json_score(
            root
        )

        raw_events = self._extract_json_events(
            parsed_payload
        )

        for raw_event in raw_events:
            event = self._parse_json_event(
                raw_event
            )

            if event is not None:
                data.events.append(
                    event
                )

        if not data.events:
            data.warnings.append(
                "JSON erkannt, aber keine "
                "Liveticker-Ereignisse gefunden."
            )

        return data

    def parse_auto(
        self,
        content: str | dict | list,
        source_url: str = "",
        match_id: str = "",
    ) -> LivetickerData:
        if isinstance(
            content,
            (dict, list),
        ):
            return self.parse_json(
                payload=content,
                source_url=source_url,
                match_id=match_id,
            )

        normalized = content.strip()

        if not normalized:
            raise ValueError(
                "Der Inhalt darf nicht leer sein."
            )

        if normalized.startswith(
            ("{", "[")
        ):
            try:
                return self.parse_json(
                    payload=normalized,
                    source_url=source_url,
                    match_id=match_id,
                )
            except json.JSONDecodeError:
                pass

        return self.parse_html(
            html=normalized,
            source_url=source_url,
            match_id=match_id,
        )

    def _parse_html_event(
        self,
        event_element: Tag,
    ) -> LivetickerEvent | None:
        text = self._clean_text(
            event_element.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            return None

        minute, additional_time = (
            self._extract_minute_from_text(
                text
            )
        )

        event_type = self._detect_event_type(
            text=text,
            raw_type=str(
                event_element.get(
                    "data-event-type",
                    "",
                )
                or ""
            ),
        )

        player = self._extract_html_player(
            event_element
        )

        player_id = self._extract_html_player_id(
            event_element
        )

        player_out = self._extract_html_player_out(
            event_element
        )

        (
            score_home,
            score_away,
        ) = self._extract_score_from_text(
            text
        )

        team = self._extract_html_team(
            event_element
        )

        return LivetickerEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=event_type,
            team=team,
            player=player,
            player_id=player_id,
            player_out=player_out,
            score_home=score_home,
            score_away=score_away,
            title=self._extract_html_title(
                event_element
            ),
            description=text,
            source_event_id=str(
                event_element.get(
                    "data-event-id",
                    "",
                )
                or ""
            ).strip(),
            raw_data={
                "classes": list(
                    event_element.get(
                        "class",
                        [],
                    )
                ),
            },
        )

    def _parse_json_event(
        self,
        raw_event: Any,
    ) -> LivetickerEvent | None:
        if not isinstance(
            raw_event,
            dict,
        ):
            return None

        description = self._get_first_text(
            raw_event,
            (
                "description",
                "text",
                "comment",
                "message",
                "content",
                "title",
            ),
        )

        raw_type = self._get_first_text(
            raw_event,
            (
                "type",
                "eventType",
                "event_type",
                "kind",
                "category",
            ),
        )

        minute = self._get_first_integer(
            raw_event,
            (
                "minute",
                "time",
                "matchMinute",
                "match_minute",
            ),
        )

        additional_time = (
            self._get_first_integer(
                raw_event,
                (
                    "additionalTime",
                    "additional_time",
                    "stoppageTime",
                ),
            )
            or 0
        )

        if minute is None and description:
            (
                minute,
                parsed_additional,
            ) = self._extract_minute_from_text(
                description
            )

            if additional_time == 0:
                additional_time = parsed_additional

        player = self._extract_json_player(
            raw_event,
            (
                "player",
                "scorer",
                "person",
                "athlete",
                "playerIn",
            ),
        )

        player_id = self._extract_json_player_id(
            raw_event,
            (
                "player",
                "scorer",
                "person",
                "athlete",
                "playerIn",
            ),
        )

        player_out = self._extract_json_player(
            raw_event,
            (
                "playerOut",
                "player_out",
                "substitutedPlayer",
            ),
        )

        player_out_id = (
            self._extract_json_player_id(
                raw_event,
                (
                    "playerOut",
                    "player_out",
                    "substitutedPlayer",
                ),
            )
        )

        team = self._extract_json_event_team(
            raw_event
        )

        score_home = self._get_first_integer(
            raw_event,
            (
                "homeScore",
                "scoreHome",
                "home_score",
            ),
        )
        score_away = self._get_first_integer(
            raw_event,
            (
                "awayScore",
                "scoreAway",
                "away_score",
            ),
        )

        event_type = self._detect_event_type(
            text=description,
            raw_type=raw_type,
        )

        return LivetickerEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=event_type,
            team=team,
            player=player,
            player_id=player_id,
            player_out=player_out,
            player_out_id=player_out_id,
            score_home=score_home,
            score_away=score_away,
            title=self._get_first_text(
                raw_event,
                (
                    "title",
                    "headline",
                    "label",
                ),
            ),
            description=description,
            source_event_id=self._get_first_text(
                raw_event,
                (
                    "id",
                    "eventId",
                    "event_id",
                    "uuid",
                ),
            ),
            raw_data=dict(
                raw_event
            ),
        )

    def _detect_event_type(
        self,
        text: str,
        raw_type: str = "",
    ) -> str:
        combined = (
            f"{raw_type} {text}"
            .strip()
            .casefold()
        )

        if any(
            keyword in combined
            for keyword in (
                "yellow-red",
                "yellow red",
                "gelb-rot",
                "gelb rote",
                "second yellow",
            )
        ):
            return self.EVENT_TYPE_YELLOW_RED_CARD

        if any(
            keyword in combined
            for keyword in (
                "red card",
                "rote karte",
                "red_card",
            )
        ):
            return self.EVENT_TYPE_RED_CARD

        if any(
            keyword in combined
            for keyword in (
                "yellow card",
                "gelbe karte",
                "yellow_card",
            )
        ):
            return self.EVENT_TYPE_YELLOW_CARD

        if any(
            keyword in combined
            for keyword in (
                "own goal",
                "eigentor",
                "own_goal",
            )
        ):
            return self.EVENT_TYPE_OWN_GOAL

        if any(
            keyword in combined
            for keyword in (
                "penalty missed",
                "elfmeter verschossen",
                "strafstoß verschossen",
                "penalty_missed",
            )
        ):
            return self.EVENT_TYPE_PENALTY_MISSED

        if any(
            keyword in combined
            for keyword in (
                "penalty goal",
                "elfmetertor",
                "strafstoßtor",
                "penalty_goal",
            )
        ):
            return self.EVENT_TYPE_PENALTY_GOAL

        if any(
            keyword in combined
            for keyword in (
                "substitution",
                "wechsel",
                "auswechslung",
                "einwechslung",
                "substitute",
            )
        ):
            return self.EVENT_TYPE_SUBSTITUTION

        if any(
            keyword in combined
            for keyword in (
                "full time",
                "fulltime",
                "abpfiff",
                "spielende",
            )
        ):
            return self.EVENT_TYPE_FULLTIME

        if any(
            keyword in combined
            for keyword in (
                "half time",
                "halftime",
                "halbzeit",
            )
        ):
            return self.EVENT_TYPE_HALFTIME

        if any(
            keyword in combined
            for keyword in (
                "kickoff",
                "anpfiff",
            )
        ):
            return self.EVENT_TYPE_KICKOFF

        if any(
            keyword in combined
            for keyword in (
                "goal",
                "tor",
                "score",
            )
        ):
            return self.EVENT_TYPE_GOAL

        if text:
            return self.EVENT_TYPE_COMMENT

        return self.EVENT_TYPE_UNKNOWN

    def _collect_html_event_elements(
        self,
        soup: BeautifulSoup,
    ) -> list[Tag]:
        elements: list[Tag] = []
        seen: set[int] = set()

        for selector in self.HTML_EVENT_SELECTORS:
            for element in soup.select(
                selector
            ):
                identity = id(
                    element
                )

                if identity in seen:
                    continue

                seen.add(
                    identity
                )
                elements.append(
                    element
                )

        return elements

    @staticmethod
    def _has_ticker_container(
        soup: BeautifulSoup,
    ) -> bool:
        selectors = (
            "#liveticker",
            "#live-ticker",
            ".liveticker",
            ".live-ticker",
            "[data-liveticker]",
            "[data-live-ticker]",
        )

        return any(
            soup.select_one(
                selector
            )
            is not None
            for selector in selectors
        )

    def _extract_teams_from_html(
        self,
        soup: BeautifulSoup,
    ) -> tuple[str, str]:
        selector_pairs = (
            (
                ".team-home .team-name",
                ".team-away .team-name",
            ),
            (
                ".home-team .team-name",
                ".away-team .team-name",
            ),
            (
                "[data-team-side='home']",
                "[data-team-side='away']",
            ),
        )

        for home_selector, away_selector in selector_pairs:
            home_element = soup.select_one(
                home_selector
            )
            away_element = soup.select_one(
                away_selector
            )

            if (
                home_element is not None
                and away_element is not None
            ):
                return (
                    self._clean_text(
                        home_element.get_text(
                            " ",
                            strip=True,
                        )
                    ),
                    self._clean_text(
                        away_element.get_text(
                            " ",
                            strip=True,
                        )
                    ),
                )

        return "", ""

    def _extract_score_from_html(
        self,
        soup: BeautifulSoup,
    ) -> tuple[int | None, int | None]:
        score_element = soup.select_one(
            ".result, .score, .match-result"
        )

        if score_element is None:
            return None, None

        return self._extract_score_from_text(
            score_element.get_text(
                " ",
                strip=True,
            )
        )

    def _extract_html_player(
        self,
        event_element: Tag,
    ) -> str:
        selectors = (
            "[data-player-name]",
            ".player-name",
            ".player",
            ".scorer",
            "[class*='player-name']",
        )

        for selector in selectors:
            element = event_element.select_one(
                selector
            )

            if element is None:
                continue

            attribute_value = str(
                element.get(
                    "data-player-name",
                    "",
                )
                or ""
            ).strip()

            if attribute_value:
                return self._clean_text(
                    attribute_value
                )

            text = self._clean_text(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                return text

        return ""

    @staticmethod
    def _extract_html_player_id(
        event_element: Tag,
    ) -> str:
        element = event_element.select_one(
            "[data-player-id], "
            "[data-user-id], "
            "a[href*='player-id'], "
            "a[href*='userid']"
        )

        if element is None:
            return ""

        for attribute in (
            "data-player-id",
            "data-user-id",
        ):
            value = str(
                element.get(
                    attribute,
                    "",
                )
                or ""
            ).strip()

            if value:
                return value

        href = str(
            element.get(
                "href",
                "",
            )
            or ""
        )

        match = re.search(
            r"/(?:player-id|userid)/([^/?#!]+)",
            href,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return ""

    def _extract_html_player_out(
        self,
        event_element: Tag,
    ) -> str:
        selectors = (
            ".player-out",
            "[data-player-out]",
            "[class*='player-out']",
        )

        for selector in selectors:
            element = event_element.select_one(
                selector
            )

            if element is None:
                continue

            text = self._clean_text(
                str(
                    element.get(
                        "data-player-out",
                        "",
                    )
                    or element.get_text(
                        " ",
                        strip=True,
                    )
                )
            )

            if text:
                return text

        return ""

    def _extract_html_team(
        self,
        event_element: Tag,
    ) -> str:
        for attribute in (
            "data-team",
            "data-team-name",
            "data-team-side",
        ):
            value = str(
                event_element.get(
                    attribute,
                    "",
                )
                or ""
            ).strip()

            if value:
                return value

        team_element = event_element.select_one(
            ".team-name, .team"
        )

        if team_element is not None:
            return self._clean_text(
                team_element.get_text(
                    " ",
                    strip=True,
                )
            )

        return ""

    def _extract_html_title(
        self,
        event_element: Tag,
    ) -> str:
        title_element = event_element.select_one(
            ".title, .headline, "
            "[class*='title']"
        )

        if title_element is None:
            return ""

        return self._clean_text(
            title_element.get_text(
                " ",
                strip=True,
            )
        )

    @staticmethod
    def _extract_page_title(
        soup: BeautifulSoup,
    ) -> str:
        title = soup.select_one(
            "title"
        )

        if title is None:
            return ""

        return title.get_text(
            " ",
            strip=True,
        )

    @staticmethod
    def _extract_minute_from_text(
        text: str,
    ) -> tuple[int | None, int]:
        match = re.search(
            r"(?<!\d)(\d{1,3})"
            r"(?:\s*\+\s*(\d{1,2}))?"
            r"\s*['’]?",
            text,
        )

        if not match:
            return None, 0

        return (
            int(match.group(1)),
            int(match.group(2) or 0),
        )

    @staticmethod
    def _extract_score_from_text(
        text: str,
    ) -> tuple[int | None, int | None]:
        match = re.search(
            r"(?<!\d)(\d+)\s*[:\-]\s*(\d+)(?!\d)",
            text,
        )

        if not match:
            return None, None

        return (
            int(match.group(1)),
            int(match.group(2)),
        )

    @staticmethod
    def _normalize_json_payload(
        payload: str | dict | list,
    ) -> dict | list:
        if isinstance(
            payload,
            str,
        ):
            return json.loads(
                payload
            )

        if isinstance(
            payload,
            (dict, list),
        ):
            return payload

        raise TypeError(
            "JSON-Payload muss str, dict "
            "oder list sein."
        )

    @staticmethod
    def _extract_json_root(
        payload: dict | list,
    ) -> dict:
        if isinstance(
            payload,
            dict,
        ):
            for key in (
                "data",
                "match",
                "game",
                "fixture",
                "result",
            ):
                value = payload.get(
                    key
                )

                if isinstance(
                    value,
                    dict,
                ):
                    return value

            return payload

        return {}

    def _extract_json_events(
        self,
        payload: dict | list,
    ) -> list[dict]:
        if isinstance(
            payload,
            list,
        ):
            return [
                item
                for item in payload
                if isinstance(
                    item,
                    dict,
                )
            ]

        queue: list[Any] = [
            payload
        ]

        while queue:
            current = queue.pop(
                0
            )

            if isinstance(
                current,
                dict,
            ):
                for key, value in current.items():
                    if (
                        key.casefold()
                        in {
                            "events",
                            "ticker",
                            "timeline",
                            "comments",
                            "entries",
                        }
                        and isinstance(
                            value,
                            list,
                        )
                    ):
                        return [
                            item
                            for item in value
                            if isinstance(
                                item,
                                dict,
                            )
                        ]

                    if isinstance(
                        value,
                        (dict, list),
                    ):
                        queue.append(
                            value
                        )

            elif isinstance(
                current,
                list,
            ):
                queue.extend(
                    current
                )

        return []

    def _extract_json_team(
        self,
        root: dict,
        side: str,
    ) -> str:
        candidates = (
            f"{side}Team",
            f"{side}_team",
            side,
        )

        for key in candidates:
            value = root.get(
                key
            )

            if isinstance(
                value,
                str,
            ):
                return self._clean_text(
                    value
                )

            if isinstance(
                value,
                dict,
            ):
                return self._get_first_text(
                    value,
                    (
                        "name",
                        "teamName",
                        "shortName",
                        "displayName",
                    ),
                )

        return ""

    def _extract_json_score(
        self,
        root: dict,
    ) -> tuple[int | None, int | None]:
        home_score = self._get_first_integer(
            root,
            (
                "homeScore",
                "scoreHome",
                "home_score",
            ),
        )
        away_score = self._get_first_integer(
            root,
            (
                "awayScore",
                "scoreAway",
                "away_score",
            ),
        )

        score = root.get(
            "score"
        )

        if isinstance(
            score,
            dict,
        ):
            if home_score is None:
                home_score = self._get_first_integer(
                    score,
                    (
                        "home",
                        "homeScore",
                    ),
                )

            if away_score is None:
                away_score = self._get_first_integer(
                    score,
                    (
                        "away",
                        "awayScore",
                    ),
                )

        return home_score, away_score

    def _extract_json_event_team(
        self,
        raw_event: dict,
    ) -> str:
        for key in (
            "team",
            "teamName",
            "club",
            "side",
        ):
            value = raw_event.get(
                key
            )

            if isinstance(
                value,
                str,
            ):
                return self._clean_text(
                    value
                )

            if isinstance(
                value,
                dict,
            ):
                return self._get_first_text(
                    value,
                    (
                        "name",
                        "teamName",
                        "displayName",
                    ),
                )

        return ""

    def _extract_json_player(
        self,
        raw_event: dict,
        keys: tuple[str, ...],
    ) -> str:
        for key in keys:
            value = raw_event.get(
                key
            )

            if isinstance(
                value,
                str,
            ):
                return self._clean_text(
                    value
                )

            if isinstance(
                value,
                dict,
            ):
                return self._get_first_text(
                    value,
                    (
                        "name",
                        "fullName",
                        "displayName",
                        "playerName",
                    ),
                )

        return ""

    @staticmethod
    def _extract_json_player_id(
        raw_event: dict,
        keys: tuple[str, ...],
    ) -> str:
        for key in keys:
            value = raw_event.get(
                key
            )

            if isinstance(
                value,
                dict,
            ):
                for id_key in (
                    "id",
                    "playerId",
                    "player_id",
                    "uuid",
                ):
                    id_value = value.get(
                        id_key
                    )

                    if id_value is not None:
                        return str(
                            id_value
                        ).strip()

        return ""

    @staticmethod
    def _get_first_text(
        source: dict,
        keys: tuple[str, ...],
    ) -> str:
        for key in keys:
            value = source.get(
                key
            )

            if isinstance(
                value,
                str,
            ):
                normalized = (
                    value.strip()
                )

                if normalized:
                    return normalized

        return ""

    @staticmethod
    def _get_first_integer(
        source: dict,
        keys: tuple[str, ...],
    ) -> int | None:
        for key in keys:
            value = source.get(
                key
            )

            if isinstance(
                value,
                bool,
            ):
                continue

            if isinstance(
                value,
                int,
            ):
                return value

            if isinstance(
                value,
                float,
            ):
                return int(
                    value
                )

            if isinstance(
                value,
                str,
            ):
                match = re.search(
                    r"-?\d+",
                    value,
                )

                if match:
                    return int(
                        match.group()
                    )

        return None

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:
        return " ".join(
            value.split()
        )