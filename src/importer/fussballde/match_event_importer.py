from __future__ import annotations

import sqlite3

from src.database.repositories.event_repository import (
    EventRepository,
)
from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.importer.fussballde.liveticker_data import (
    LivetickerData,
    LivetickerEvent,
)
from src.importer.fussballde.match_notes_builder import (
    MatchNotesBuilder,
)
from src.importer.fussballde.parsers.match_detail_data import (
    MatchDetailData,
    MatchEvent,
)
from src.importer.fussballde.parsers.match_detail_parser import (
    MatchDetailParser,
)


class MatchEventImporter:
    """
    Importiert Spielereignisse aus Match-HTML oder Liveticker.

    Zuständig für:
    - Tore
    - Eigentore
    - Karten
    - Elfmeter
    - Ein-/Auswechslungen
    - Spielerauflösung
    - Teamauflösung
    """

    EVENT_TYPE_MAPPING = {
        MatchDetailParser.EVENT_GOAL: "GOAL",
        MatchDetailParser.EVENT_OWN_GOAL: "OWN_GOAL",
        MatchDetailParser.EVENT_YELLOW_CARD:
            "YELLOW_CARD",
        MatchDetailParser.EVENT_SECOND_YELLOW_CARD:
            "YELLOW_RED_CARD",
        MatchDetailParser.EVENT_RED_CARD:
            "RED_CARD",
        MatchDetailParser.EVENT_PENALTY_MISSED:
            "PENALTY_MISSED",
    }

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

        self.event_repository = EventRepository(
            connection
        )

        self.player_repository = PlayerRepository(
            connection
        )

    def import_events(
        self,
        match_id: int,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
        liveticker_data: LivetickerData | None = None,
    ) -> tuple[int, set[int]]:
        if liveticker_data is not None:
            return self._import_liveticker_events(
                match_id=match_id,
                liveticker_data=liveticker_data,
                detail_data=detail_data,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
            )

        return self._import_html_events(
            match_id=match_id,
            detail_data=detail_data,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )

    def _import_liveticker_events(
        self,
        match_id: int,
        liveticker_data: LivetickerData,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> tuple[int, set[int]]:
        prepared_events: list[dict] = []

        for event in liveticker_data.events:
            team_id = (
                self._resolve_liveticker_team_id(
                    event=event,
                    detail_data=detail_data,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                )
            )

            if event.event_type == "substitution":
                prepared_events.extend(
                    self._prepare_liveticker_substitution(
                        event=event,
                        team_id=team_id,
                    )
                )
                continue

            prepared_event = (
                self._prepare_liveticker_event(
                    event=event,
                    team_id=team_id,
                )
            )

            if prepared_event is not None:
                prepared_events.append(
                    prepared_event
                )

        imported_event_count = (
            self.event_repository
            .replace_match_events(
                match_id=match_id,
                events=prepared_events,
            )
        )

        player_ids = self._collect_player_ids(
            prepared_events
        )

        return (
            imported_event_count,
            player_ids,
        )

    def _prepare_liveticker_event(
        self,
        event: LivetickerEvent,
        team_id: int | None,
    ) -> dict | None:
        event_type_mapping = {
            "goal": "GOAL",
            "penalty_goal": "PENALTY_GOAL",
            "yellow_card": "YELLOW_CARD",
            "yellow_red_card": "YELLOW_RED_CARD",
            "red_card": "RED_CARD",
        }

        event_type_code = (
            event_type_mapping.get(
                event.event_type
            )
        )

        if event_type_code is None:
            return None

        player_id = self._get_or_create_player(
            player_name=event.player,
            external_id=event.player_id,
            team_id=team_id,
        )

        return {
            "event_type_code": event_type_code,
            "minute": event.minute,
            "second": 0,
            "team_id": team_id,
            "player_id": player_id,
            "related_player_id": None,
            "value": (
                self._build_liveticker_value(
                    event
                )
            ),
            "notes": (
                MatchNotesBuilder
                .clean_import_text(
                    event.description,
                    allow_private_unicode=False,
                )
            ),
        }

    def _prepare_liveticker_substitution(
        self,
        event: LivetickerEvent,
        team_id: int | None,
    ) -> list[dict]:
        player_in_id = (
            self._get_or_create_player(
                player_name=event.player,
                external_id=event.player_id,
                team_id=team_id,
            )
        )

        player_out_id = (
            self._get_or_create_player(
                player_name=event.player_out,
                external_id=event.player_out_id,
                team_id=team_id,
            )
        )

        description = (
            MatchNotesBuilder
            .clean_import_text(
                event.description,
                allow_private_unicode=False,
            )
        )

        events: list[dict] = []

        if player_out_id is not None:
            events.append(
                {
                    "event_type_code":
                        "SUBSTITUTION_OUT",
                    "minute": event.minute,
                    "second": 0,
                    "team_id": team_id,
                    "player_id": player_out_id,
                    "related_player_id":
                        player_in_id,
                    "value": (
                        self._build_liveticker_substitution_value(
                            direction="out",
                            event=event,
                        )
                    ),
                    "notes": description,
                }
            )

        if player_in_id is not None:
            events.append(
                {
                    "event_type_code":
                        "SUBSTITUTION_IN",
                    "minute": event.minute,
                    "second": 0,
                    "team_id": team_id,
                    "player_id": player_in_id,
                    "related_player_id":
                        player_out_id,
                    "value": (
                        self._build_liveticker_substitution_value(
                            direction="in",
                            event=event,
                        )
                    ),
                    "notes": description,
                }
            )

        return events

    def _resolve_liveticker_team_id(
        self,
        event: LivetickerEvent,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> int | None:
        event_team = self._normalize_name(
            event.team
        )

        if not event_team:
            return None

        home_names = {
            self._normalize_name(
                detail_data.home_team
            ),
        }

        away_names = {
            self._normalize_name(
                detail_data.away_team
            ),
        }

        if event_team in home_names:
            return home_team_id

        if event_team in away_names:
            return away_team_id

        return None

    @staticmethod
    def _build_liveticker_value(
        event: LivetickerEvent,
    ) -> str:
        values = [
            "source:liveticker"
        ]

        if event.has_score:
            values.append(
                f"{event.score_home}:"
                f"{event.score_away}"
            )

        if event.additional_time > 0:
            values.append(
                "Nachspielzeit:"
                f"{event.additional_time}"
            )

        return " | ".join(
            values
        )

    @staticmethod
    def _build_liveticker_substitution_value(
        direction: str,
        event: LivetickerEvent,
    ) -> str:
        values = [
            f"substitution_{direction}",
            "source:liveticker",
        ]

        if event.additional_time > 0:
            values.append(
                "Nachspielzeit:"
                f"{event.additional_time}"
            )

        return " | ".join(
            values
        )

    def _import_html_events(
        self,
        match_id: int,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> tuple[int, set[int]]:
        prepared_events = self._prepare_html_events(
            detail_data=detail_data,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )

        imported_event_count = (
            self.event_repository
            .replace_match_events(
                match_id=match_id,
                events=prepared_events,
            )
        )

        player_ids = self._collect_player_ids(
            prepared_events
        )

        return (
            imported_event_count,
            player_ids,
        )

    def _prepare_html_events(
        self,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> list[dict]:
        prepared_events: list[dict] = []

        for event in detail_data.events:
            team_id = self._resolve_html_team_id(
                event=event,
                detail_data=detail_data,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
            )

            if (
                event.event_type
                == MatchDetailParser.EVENT_SUBSTITUTION
            ):
                prepared_events.extend(
                    self._prepare_html_substitution(
                        event=event,
                        team_id=team_id,
                    )
                )
                continue

            prepared_event = self._prepare_html_event(
                event=event,
                team_id=team_id,
            )

            if prepared_event is not None:
                prepared_events.append(
                    prepared_event
                )

        return prepared_events

    def _prepare_html_event(
        self,
        event: MatchEvent,
        team_id: int | None,
    ) -> dict | None:
        event_type_code = (
            self.EVENT_TYPE_MAPPING.get(
                event.event_type
            )
        )

        if (
            event.event_type
            == MatchDetailParser.EVENT_GOAL
            and event.value == "penalty_goal"
        ):
            event_type_code = "PENALTY_GOAL"

        if event_type_code is None:
            return None

        player_id = self._get_or_create_player(
            player_name=event.player,
            external_id=event.player_id,
            team_id=team_id,
        )

        return {
            "event_type_code": event_type_code,
            "minute": event.minute,
            "second": 0,
            "team_id": team_id,
            "player_id": player_id,
            "related_player_id": None,
            "value": self._build_html_event_value(
                event
            ),
            "notes": (
                MatchNotesBuilder
                .clean_import_text(
                    event.description,
                    allow_private_unicode=False,
                )
            ),
        }

    def _prepare_html_substitution(
        self,
        event: MatchEvent,
        team_id: int | None,
    ) -> list[dict]:
        player_in_id = self._get_or_create_player(
            player_name=event.player,
            external_id=event.player_id,
            team_id=team_id,
        )

        player_out_id = self._get_or_create_player(
            player_name=event.player_out,
            external_id=event.player_out_id,
            team_id=team_id,
        )

        description = (
            MatchNotesBuilder
            .clean_import_text(
                event.description,
                allow_private_unicode=False,
            )
        )

        events: list[dict] = []

        if player_out_id is not None:
            events.append(
                {
                    "event_type_code":
                        "SUBSTITUTION_OUT",
                    "minute": event.minute,
                    "second": 0,
                    "team_id": team_id,
                    "player_id": player_out_id,
                    "related_player_id":
                        player_in_id,
                    "value": (
                        self._build_html_substitution_value(
                            direction="out",
                            event=event,
                        )
                    ),
                    "notes": description,
                }
            )

        if player_in_id is not None:
            events.append(
                {
                    "event_type_code":
                        "SUBSTITUTION_IN",
                    "minute": event.minute,
                    "second": 0,
                    "team_id": team_id,
                    "player_id": player_in_id,
                    "related_player_id":
                        player_out_id,
                    "value": (
                        self._build_html_substitution_value(
                            direction="in",
                            event=event,
                        )
                    ),
                    "notes": description,
                }
            )

        return events

    def _get_or_create_player(
        self,
        player_name: str,
        external_id: str,
        team_id: int | None,
    ) -> int | None:
        normalized_name = (
            MatchNotesBuilder
            .clean_import_text(
                player_name
            )
        )

        normalized_external_id = (
            external_id.strip()
        )

        if (
            not normalized_name
            and not normalized_external_id
        ):
            return None

        first_name, last_name = (
            self._split_player_name(
                normalized_name
            )
        )

        if not last_name:
            if normalized_external_id:
                last_name = (
                    "Unbekannt "
                    f"{normalized_external_id}"
                )
            else:
                return None

        return self.player_repository.get_or_create(
            first_name=first_name,
            last_name=last_name,
            team_id=team_id,
            external_id=normalized_external_id,
            commit=False,
        )

    def _resolve_html_team_id(
        self,
        event: MatchEvent,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> int | None:
        event_team = self._normalize_name(
            event.team
        )

        home_team = self._normalize_name(
            detail_data.home_team
        )

        away_team = self._normalize_name(
            detail_data.away_team
        )

        if event_team and event_team == home_team:
            return home_team_id

        if event_team and event_team == away_team:
            return away_team_id

        return None

    @staticmethod
    def _split_player_name(
        player_name: str,
    ) -> tuple[str, str]:
        normalized_name = " ".join(
            player_name.split()
        )

        if not normalized_name:
            return "", ""

        parts = normalized_name.split(" ")

        if len(parts) == 1:
            return "", parts[0]

        first_name = " ".join(
            parts[:-1]
        )

        last_name = parts[-1]

        return first_name, last_name

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        return " ".join(
            value.split()
        ).casefold()

    @staticmethod
    def _build_html_event_value(
        event: MatchEvent,
    ) -> str:
        values: list[str] = []

        if event.value:
            values.append(
                event.value
            )

        if (
            event.home_goals is not None
            and event.away_goals is not None
        ):
            values.append(
                f"{event.home_goals}:"
                f"{event.away_goals}"
            )

        if event.additional_time > 0:
            values.append(
                "Nachspielzeit:"
                f"{event.additional_time}"
            )

        return " | ".join(
            values
        )

    @staticmethod
    def _build_html_substitution_value(
        direction: str,
        event: MatchEvent,
    ) -> str:
        values = [
            f"substitution_{direction}"
        ]

        if event.additional_time > 0:
            values.append(
                "Nachspielzeit:"
                f"{event.additional_time}"
            )

        return " | ".join(
            values
        )

    @staticmethod
    def _collect_player_ids(
        prepared_events: list[dict],
    ) -> set[int]:
        player_ids: set[int] = {
            int(event["player_id"])
            for event in prepared_events
            if event.get(
                "player_id"
            ) is not None
        }

        player_ids.update(
            int(
                event["related_player_id"]
            )
            for event in prepared_events
            if event.get(
                "related_player_id"
            ) is not None
        )

        return player_ids