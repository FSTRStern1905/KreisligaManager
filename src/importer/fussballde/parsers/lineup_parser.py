from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.font_decoder import FontDecoder
from src.importer.fussballde.parsers.lineup_data import (
    LineupPlayer,
    MatchLineup,
    TeamLineup,
)


class LineupParser:
    def __init__(
        self,
        request_context: Any | None = None,
    ) -> None:
        self.request_context = request_context
        self.font_decoder = (
            FontDecoder(request_context)
            if request_context is not None
            else None
        )

    def parse(
        self,
        html: str,
    ) -> MatchLineup:
        normalized_html = html.strip()

        if not normalized_html:
            raise ValueError(
                "Der HTML-Inhalt der Aufstellung darf "
                "nicht leer sein."
            )

        soup = BeautifulSoup(
            normalized_html,
            "html.parser",
        )

        home_team_name = self._parse_team_name(
            soup=soup,
            side="home",
        )

        away_team_name = self._parse_team_name(
            soup=soup,
            side="away",
        )

        home_lineup = TeamLineup(
            team_name=home_team_name,
        )

        away_lineup = TeamLineup(
            team_name=away_team_name,
        )

        home_lineup.starting = self._parse_players(
            soup=soup,
            selector=(
                ".match-lineup .starting "
                "a.player-wrapper.home"
            ),
            team_name=home_team_name,
            is_starting=True,
        )

        away_lineup.starting = self._parse_players(
            soup=soup,
            selector=(
                ".match-lineup .starting "
                "a.player-wrapper.away"
            ),
            team_name=away_team_name,
            is_starting=True,
        )

        home_lineup.substitutes = self._parse_players(
            soup=soup,
            selector=(
                ".match-lineup .substitutes "
                "a.player-wrapper.home"
            ),
            team_name=home_team_name,
            is_starting=False,
        )

        away_lineup.substitutes = self._parse_players(
            soup=soup,
            selector=(
                ".match-lineup .substitutes "
                "a.player-wrapper.away"
            ),
            team_name=away_team_name,
            is_starting=False,
        )

        home_lineup.coach = self._parse_coach(
            soup=soup,
            side="home",
        )

        away_lineup.coach = self._parse_coach(
            soup=soup,
            side="away",
        )

        return MatchLineup(
            home=home_lineup,
            away=away_lineup,
        )

    def _parse_team_name(
        self,
        soup: BeautifulSoup,
        side: str,
    ) -> str:
        element = soup.select_one(
            f".match-lineup .head .{side} "
            ".club-name a"
        )

        if element is None:
            return ""

        return self._clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

    def _parse_players(
        self,
        soup: BeautifulSoup,
        selector: str,
        team_name: str,
        is_starting: bool,
    ) -> list[LineupPlayer]:
        players: list[LineupPlayer] = []

        for player_element in soup.select(
            selector
        ):
            player = self._parse_player(
                player_element=player_element,
                team_name=team_name,
                is_starting=is_starting,
            )

            if player is not None:
                players.append(
                    player
                )

        return players

    def _parse_player(
        self,
        player_element: Tag,
        team_name: str,
        is_starting: bool,
    ) -> LineupPlayer | None:
        external_id = self._extract_player_id(
            player_element
        )

        first_name = self._decode_name_part(
            player_element.select_one(
                ".player-name .firstname"
            )
        )

        last_name = self._decode_name_part(
            player_element.select_one(
                ".player-name .lastname"
            )
        )

        if (
            not external_id
            and not first_name
            and not last_name
        ):
            return None

        shirt_number = self._parse_shirt_number(
            player_element
        )

        is_goalkeeper = (
            player_element.select_one(
                ".goal-keeper"
            )
            is not None
        )

        captain_text = self._clean_text(
            player_element.select_one(
                ".captain .c"
            ).get_text(
                " ",
                strip=True,
            )
        ) if player_element.select_one(
            ".captain .c"
        ) is not None else ""

        is_captain = (
            captain_text.upper() == "C"
        )

        if (
            captain_text.upper() == "T"
            and not is_goalkeeper
        ):
            is_goalkeeper = True

        return LineupPlayer(
            external_id=external_id,
            first_name=first_name,
            last_name=last_name,
            shirt_number=shirt_number,
            is_starting=is_starting,
            is_substitute=not is_starting,
            is_goalkeeper=is_goalkeeper,
            is_captain=is_captain,
            team_name=team_name,
        )

    def _parse_coach(
        self,
        soup: BeautifulSoup,
        side: str,
    ) -> str:
        coach_element = soup.select_one(
            f".match-lineup .trainer "
            f".group.{side} "
            ".player-name"
        )

        if coach_element is None:
            return ""

        first_name = self._decode_name_part(
            coach_element.select_one(
                ".firstname"
            )
        )

        last_name = self._decode_name_part(
            coach_element.select_one(
                ".lastname"
            )
        )

        return self._clean_text(
            " ".join(
                part
                for part in (
                    first_name,
                    last_name,
                )
                if part
            )
        )

    def _decode_name_part(
        self,
        element: Tag | None,
    ) -> str:
        if element is None:
            return ""

        raw_text = element.get_text(
            " ",
            strip=True,
        )

        if not raw_text:
            return ""

        font_id = str(
            element.get(
                "data-obfuscation",
                "",
            )
            or ""
        ).strip()

        if (
            self.font_decoder is not None
            and font_id
        ):
            try:
                raw_text = self.font_decoder.decode(
                    text=raw_text,
                    font_id=font_id,
                )
            except Exception:
                pass

        decoded_text = self._clean_text(
            raw_text
        )

        if self._contains_private_unicode(
            decoded_text
        ):
            return ""

        return decoded_text

    @staticmethod
    def _parse_shirt_number(
        player_element: Tag,
    ) -> int | None:
        number_element = (
            player_element.select_one(
                ".player-number"
            )
        )

        if number_element is None:
            return None

        text = number_element.get_text(
            " ",
            strip=True,
        )

        match = re.search(
            r"\d+",
            text,
        )

        if match is None:
            return None

        return int(
            match.group()
        )

    @staticmethod
    def _extract_player_id(
        player_element: Tag,
    ) -> str:
        href = str(
            player_element.get(
                "href",
                "",
            )
            or ""
        )

        patterns = [
            r"/player-id/([^/?#!]+)",
            r"/userid/([^/?#!]+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                href,
                re.IGNORECASE,
            )

            if match is not None:
                return match.group(1)

        return ""

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:
        return " ".join(
            (value or "").split()
        ).strip()

    @staticmethod
    def _contains_private_unicode(
        value: str,
    ) -> bool:
        return any(
            0xE000 <= ord(character) <= 0xF8FF
            for character in value
        )