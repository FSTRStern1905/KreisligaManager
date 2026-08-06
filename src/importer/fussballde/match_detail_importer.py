from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.database.repositories.event_repository import (
    EventRepository,
)
from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.database.repositories.referee_repository import (
    RefereeRepository,
)
from src.database.repositories.stadium_repository import (
    StadiumRepository,
)
from src.importer.fussballde.parsers.match_detail_data import (
    MatchDetailData,
    MatchEvent,
)
from src.importer.fussballde.parsers.match_detail_parser import (
    MatchDetailParser,
)

from src.importer.fussballde.lineup_importer import (
    LineupImporter,
)
from src.importer.fussballde.liveticker_data import (
    LivetickerData,
    LivetickerEvent,
)
from src.importer.fussballde.liveticker_json_parser import (
    LivetickerJsonParser,
)

from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)

class MatchDetailImporter:
    DEBUG_HTML_PATH = Path(
        "debug/html/matches"
    )
    DEBUG_LIVETICKER_PATH = Path(
        "debug/liveticker/json"
    )

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

        self.match_repository = MatchRepository(
            connection
        )
        self.player_repository = PlayerRepository(
            connection
        )
        self.event_repository = EventRepository(
            connection
        )
        self.referee_repository = RefereeRepository(
            connection
        )
        self.stadium_repository = StadiumRepository(
            connection
        )
        self.lineup_importer = LineupImporter(
            connection
        )
        self.player_match_stats_builder = PlayerMatchStatsBuilder(
            connection
        )
        self.liveticker_json_parser = (
            LivetickerJsonParser()
        )

    def import_from_page(
        self,
        page: Any,
        source_url: str,
    ) -> dict:
        if page is None:
            raise ValueError(
                "Es wurde keine Browserseite übergeben."
            )

        normalized_url = source_url.strip()

        if not normalized_url:
            raise ValueError(
                "Die Spiel-URL darf nicht leer sein."
            )

        page.goto(
            normalized_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        try:
            page.wait_for_load_state(
                "networkidle",
                timeout=20_000,
            )
        except Exception:
            pass

        page.wait_for_timeout(
            3_000
        )

        html = page.content()

        self._save_debug_html(
            html=html,
            source_url=normalized_url,
        )

        parser = MatchDetailParser(
            page
        )

        detail_data = parser.parse(
            html=html,
            source_url=normalized_url,
        )

        lineup_result = (
            self.lineup_importer
            .import_from_page(
                page=page,
                match_external_id=(
                    detail_data.match_id
                ),
            )
        )

        liveticker_data = (
            self._load_liveticker_data(
                page=page,
                source_url=normalized_url,
                match_external_id=(
                    detail_data.match_id
                ),
            )
        )

        result = self.import_data(
            detail_data=detail_data,
            source_url=normalized_url,
            liveticker_data=liveticker_data,
        )

        result["lineups_imported"] = (
            lineup_result[
                "lineups_imported"
            ]
        )

        result[
            "lineup_players_imported"
        ] = lineup_result[
            "players_imported"
        ]

        result["liveticker_available"] = (
            liveticker_data is not None
        )

        result["event_source"] = (
            "liveticker_json"
            if liveticker_data is not None
            else "match_html"
        )

        return result

    def _load_liveticker_data(
        self,
        page: Any,
        source_url: str,
        match_external_id: str,
    ) -> LivetickerData | None:
        payloads: list[dict] = []

        def handle_response(
            response: Any,
        ) -> None:
            response_url = str(
                response.url
            )

            if (
                "ajax.liveticker"
                not in response_url.casefold()
            ):
                return

            if (
                match_external_id
                and match_external_id
                not in response_url
            ):
                return

            try:
                payload = response.json()
            except Exception:
                return

            if (
                isinstance(payload, dict)
                and isinstance(
                    payload.get(
                        "events"
                    ),
                    list,
                )
            ):
                payloads.append(
                    payload
                )

        page.on(
            "response",
            handle_response,
        )

        try:
            liveticker_url = (
                self._build_liveticker_url(
                    source_url
                )
            )

            page.goto(
                liveticker_url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=20_000,
                )
            except Exception:
                pass

            page.wait_for_timeout(
                4_000
            )

        except Exception:
            return None

        finally:
            try:
                page.remove_listener(
                    "response",
                    handle_response,
                )
            except Exception:
                pass

        if not payloads:
            return None

        payload = max(
            payloads,
            key=lambda item: len(
                item.get(
                    "events",
                    [],
                )
            ),
        )

        self._save_liveticker_json(
            match_external_id=(
                match_external_id
            ),
            payload=payload,
        )

        try:
            data = (
                self.liveticker_json_parser
                .parse(
                    payload=payload,
                    source_url=(
                        self._build_liveticker_url(
                            source_url
                        )
                    ),
                )
            )
        except Exception:
            return None

        if not self._has_importable_liveticker_events(
            data
        ):
            return None

        return data

    @staticmethod
    def _build_liveticker_url(
        source_url: str,
    ) -> str:
        normalized_url = (
            source_url
            .split(
                "#",
                1,
            )[0]
            .split(
                "?",
                1,
            )[0]
            .rstrip(
                "/"
            )
        )

        if "/tab/" in normalized_url:
            normalized_url = (
                normalized_url
                .split(
                    "/tab/",
                    1,
                )[0]
            )

        return (
            f"{normalized_url}"
            "/tab/liveTicker/"
        )

    def _save_liveticker_json(
        self,
        match_external_id: str,
        payload: dict,
    ) -> Path:
        self.DEBUG_LIVETICKER_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_match_id = (
            match_external_id.strip()
            or "unknown_match"
        )

        file_path = (
            self.DEBUG_LIVETICKER_PATH
            / f"{safe_match_id}.json"
        )

        file_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return file_path

    @staticmethod
    def _has_importable_liveticker_events(
        data: LivetickerData,
    ) -> bool:
        importable_types = {
            "goal",
            "yellow_card",
            "yellow_red_card",
            "red_card",
            "substitution",
        }

        return any(
            event.event_type
            in importable_types
            for event in data.events
        )

    def _save_debug_html(
        self,
        html: str,
        source_url: str,
    ) -> Path:
        match_id = self._extract_match_id_from_url(
            source_url
        )

        if not match_id:
            match_id = "unknown_match"

        self.DEBUG_HTML_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = self.DEBUG_HTML_PATH / (
            f"{match_id}.html"
        )

        file_path.write_text(
            html,
            encoding="utf-8",
        )

        return file_path

    @staticmethod
    def _extract_match_id_from_url(
        source_url: str,
    ) -> str:
        normalized_url = source_url.strip()

        if not normalized_url:
            return ""

        marker = "/spiel/"

        if marker not in normalized_url:
            return ""

        match_id = normalized_url.rsplit(
            marker,
            1,
        )[-1]

        match_id = match_id.split(
            "/",
            1,
        )[0]

        match_id = match_id.split(
            "?",
            1,
        )[0]

        match_id = match_id.split(
            "#",
            1,
        )[0]

        return match_id.strip()

    def import_from_html(
        self,
        html: str,
        source_url: str,
        page: Any = None,
    ) -> dict:
        normalized_html = html.strip()
        normalized_url = source_url.strip()

        if not normalized_html:
            raise ValueError(
                "Der HTML-Inhalt darf nicht leer sein."
            )

        if not normalized_url:
            raise ValueError(
                "Die Spiel-URL darf nicht leer sein."
            )

        parser = MatchDetailParser(page)

        detail_data = parser.parse(
            html=normalized_html,
            source_url=normalized_url,
        )

        return self.import_data(
            detail_data=detail_data,
            source_url=normalized_url,
        )

    def import_data(
        self,
        detail_data: MatchDetailData,
        source_url: str = "",
        liveticker_data: LivetickerData | None = None,
    ) -> dict:
        external_id = detail_data.match_id.strip()

        if not external_id:
            raise ValueError(
                "Die externe Spiel-ID konnte nicht "
                "ermittelt werden."
            )

        database_match = (
            self.match_repository.get_by_external_id(
                external_id
            )
        )

        if database_match is None:
            raise ValueError(
                "Das Spiel wurde nicht in der Datenbank "
                f"gefunden: {external_id}"
            )

        if database_match.match_id is None:
            raise ValueError(
                "Das gefundene Spiel besitzt keine "
                "interne Spiel-ID."
            )

        if database_match.home_team_id is None:
            raise ValueError(
                "Das Spiel besitzt keine "
                "Heimmannschaft."
            )

        if database_match.away_team_id is None:
            raise ValueError(
                "Das Spiel besitzt keine "
                "Auswärtsmannschaft."
            )

        match_id = int(
            database_match.match_id
        )

        self._validate_teams(
            detail_data=detail_data,
            database_match=database_match,
        )

        try:
            stadium_id = self._import_stadium(
                detail_data.stadium
            )

            referee_id = self._import_referee(
                detail_data.referee
            )

            database_match.stadium_id = stadium_id
            database_match.referee_id = referee_id

            self._update_match(
                database_match=database_match,
                detail_data=detail_data,
                source_url=source_url,
            )

            if liveticker_data is not None:
                (
                    imported_event_count,
                    player_ids,
                ) = self._import_liveticker_events(
                    match_id=match_id,
                    liveticker_data=liveticker_data,
                    detail_data=detail_data,
                    home_team_id=int(
                        database_match.home_team_id
                    ),
                    away_team_id=int(
                        database_match.away_team_id
                    ),
                )
            else:
                (
                    imported_event_count,
                    player_ids,
                ) = self._import_events(
                    match_id=match_id,
                    detail_data=detail_data,
                    home_team_id=int(
                        database_match.home_team_id
                    ),
                    away_team_id=int(
                        database_match.away_team_id
                    ),
                )

            player_match_stats_result = (
                self.player_match_stats_builder.build(
                    match_id
                )
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        return {
            "match_id": match_id,
            "external_id": external_id,
            "home_team": detail_data.home_team,
            "away_team": detail_data.away_team,
            "home_goals": detail_data.home_goals,
            "away_goals": detail_data.away_goals,
            "stadium_id": stadium_id,
            "referee_id": referee_id,
            "players_imported": len(player_ids),
            "events_imported":
                imported_event_count,
            "event_source": (
                "liveticker_json"
                if liveticker_data is not None
                else "match_html"
            ),
            "player_match_stats_created": (
                player_match_stats_result[
                    "stats_created"
                ]
            ),
        }    

    def _update_match(
        self,
        database_match,
        detail_data: MatchDetailData,
        source_url: str,
    ) -> None:
        if detail_data.home_goals is not None:
            database_match.home_goals = (
                detail_data.home_goals
            )

        if detail_data.away_goals is not None:
            database_match.away_goals = (
                detail_data.away_goals
            )

        if detail_data.attendance is not None:
            database_match.attendance = (
                detail_data.attendance
            )

        if (
            detail_data.home_goals is not None
            and detail_data.away_goals is not None
        ):
            database_match.status = "finished"

        database_match.notes = (
            self._build_match_notes(
                existing_notes=database_match.notes,
                detail_data=detail_data,
                source_url=source_url,
            )
        )
        database_match.detail_imported = 1
        
        self.match_repository.update(
            database_match
        )

    def _import_stadium(
        self,
        stadium_name: str,
    ) -> int | None:
        normalized_name = self._clean_import_text(
            stadium_name
        )

        if not normalized_name:
            return None

        return self.stadium_repository.get_or_create(
            name=normalized_name,
            commit=False,
        )

    def _import_referee(
        self,
        referee_name: str,
    ) -> int | None:
        normalized_name = self._clean_import_text(
            referee_name
        )

        normalized_name = self._remove_referee_suffixes(
            normalized_name
        )

        if not normalized_name:
            return None

        return (
            self.referee_repository
            .get_or_create_by_full_name(
                full_name=normalized_name,
                commit=False,
            )
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

        player_ids: set[int] = {
            int(event["player_id"])
            for event in prepared_events
            if event.get(
                "player_id"
            ) is not None
        }

        player_ids.update(
            int(
                event[
                    "related_player_id"
                ]
            )
            for event in prepared_events
            if event.get(
                "related_player_id"
            ) is not None
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
            "yellow_card": "YELLOW_CARD",
            "yellow_red_card": (
                "YELLOW_RED_CARD"
            ),
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
            "event_type_code": (
                event_type_code
            ),
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
            "notes": self._clean_import_text(
                event.description,
                allow_private_unicode=False,
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

        description = self._clean_import_text(
            event.description,
            allow_private_unicode=False,
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

    def _import_events(
        self,
        match_id: int,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> tuple[int, set[int]]:
        prepared_events = self._prepare_events(
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

        player_ids: set[int] = {
            int(event["player_id"])
            for event in prepared_events
            if event.get("player_id") is not None
        }

        player_ids.update(
            int(event["related_player_id"])
            for event in prepared_events
            if event.get(
                "related_player_id"
            ) is not None
        )

        return (
            imported_event_count,
            player_ids,
        )

    def _prepare_events(
        self,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> list[dict]:
        prepared_events: list[dict] = []

        for event in detail_data.events:
            team_id = self._resolve_team_id(
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
                    self._prepare_substitution(
                        event=event,
                        team_id=team_id,
                    )
                )

                continue

            prepared_event = self._prepare_event(
                event=event,
                team_id=team_id,
            )

            if prepared_event is not None:
                prepared_events.append(
                    prepared_event
                )

        return prepared_events

    def _prepare_event(
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
            "value": self._build_event_value(
                event
            ),
            "notes": self._clean_import_text(
                event.description,
                allow_private_unicode=False,
            ),
        }

    def _prepare_substitution(
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

        description = self._clean_import_text(
            event.description,
            allow_private_unicode=False,
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
                    "value": self._build_substitution_value(
                        direction="out",
                        event=event,
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
                    "value": self._build_substitution_value(
                        direction="in",
                        event=event,
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
        normalized_name = self._clean_import_text(
            player_name
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

    def _resolve_team_id(
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

    def _validate_teams(
        self,
        detail_data: MatchDetailData,
        database_match,
    ) -> None:
        parsed_home = self._normalize_name(
            detail_data.home_team
        )

        parsed_away = self._normalize_name(
            detail_data.away_team
        )

        database_home = self._normalize_name(
            database_match.home_team_name
        )

        database_away = self._normalize_name(
            database_match.away_team_name
        )

        if (
            parsed_home
            and database_home
            and parsed_home != database_home
        ):
            raise ValueError(
                "Die Heimmannschaft der Detailseite "
                "passt nicht zum gespeicherten Spiel:\n"
                f"{detail_data.home_team} != "
                f"{database_match.home_team_name}"
            )

        if (
            parsed_away
            and database_away
            and parsed_away != database_away
        ):
            raise ValueError(
                "Die Auswärtsmannschaft der Detailseite "
                "passt nicht zum gespeicherten Spiel:\n"
                f"{detail_data.away_team} != "
                f"{database_match.away_team_name}"
            )

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
    def _build_event_value(
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

        return " | ".join(values)

    @staticmethod
    def _build_substitution_value(
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

        return " | ".join(values)

    @classmethod
    def _build_match_notes(
        cls,
        existing_notes: str,
        detail_data: MatchDetailData,
        source_url: str,
    ) -> str:
        notes: list[str] = []

        existing_lines = (
            existing_notes.splitlines()
            if existing_notes
            else []
        )

        managed_prefixes = (
            "Halbzeit:",
            "Spielstätte:",
            "Schiedsrichter:",
            "fussball.de:",
        )

        for line in existing_lines:
            normalized_line = line.strip()

            if not normalized_line:
                continue

            if normalized_line.startswith(
                managed_prefixes
            ):
                continue

            if cls._contains_private_unicode(
                normalized_line
            ):
                continue

            notes.append(
                normalized_line
            )

        if (
            detail_data.halftime_home is not None
            and detail_data.halftime_away is not None
        ):
            notes.append(
                "Halbzeit: "
                f"{detail_data.halftime_home}:"
                f"{detail_data.halftime_away}"
            )

        stadium = cls._clean_import_text(
            detail_data.stadium
        )

        if stadium:
            notes.append(
                f"Spielstätte: {stadium}"
            )

        referee = cls._clean_import_text(
            detail_data.referee
        )

        referee = cls._remove_referee_suffixes(
            referee
        )

        if referee:
            notes.append(
                f"Schiedsrichter: {referee}"
            )

        normalized_url = source_url.strip()

        if normalized_url:
            notes.append(
                f"fussball.de: {normalized_url}"
            )

        return "\n".join(
            dict.fromkeys(notes)
        )

    @classmethod
    def _clean_import_text(
        cls,
        value: str,
        allow_private_unicode: bool = False,
    ) -> str:
        normalized = " ".join(
            (value or "").split()
        )

        if not normalized:
            return ""

        if (
            not allow_private_unicode
            and cls._contains_private_unicode(
                normalized
            )
        ):
            return ""

        return normalized.strip(
            " -|,;"
        )

    @staticmethod
    def _contains_private_unicode(
        value: str,
    ) -> bool:
        return any(
            0xE000 <= ord(character) <= 0xF8FF
            for character in value
        )

    @staticmethod
    def _remove_referee_suffixes(
        referee_name: str,
    ) -> str:
        normalized_name = referee_name.strip()

        suffixes = (
            " Assistenten:",
            " Assistent:",
            " Schiedsrichterassistenten:",
            " Schiedsrichter-Assistenten:",
        )

        for suffix in suffixes:
            position = normalized_name.casefold().find(
                suffix.casefold()
            )

            if position >= 0:
                normalized_name = (
                    normalized_name[:position]
                ).strip()

        return normalized_name