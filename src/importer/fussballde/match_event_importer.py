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

        self._liveticker_team_cache: dict[
            tuple[int, str],
            int,
        ] = {}

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

        self._seed_liveticker_team_cache(
            match_id=match_id,
            liveticker_data=liveticker_data,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )

        self._hydrate_liveticker_players(
            match_id=match_id,
            liveticker_data=liveticker_data,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )

        for event in liveticker_data.events:
            team_id = (
                self._resolve_liveticker_team_id(
                    match_id=match_id,
                    event=event,
                    detail_data=detail_data,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                )
            )

            if event.event_type == "substitution":
                prepared_events.extend(
                    self._prepare_liveticker_substitution(
                        match_id=match_id,
                        event=event,
                        team_id=team_id,
                    )
                )
                continue

            prepared_event = (
                self._prepare_liveticker_event(
                    match_id=match_id,
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

    def _hydrate_liveticker_players(
        self,
        match_id: int,
        liveticker_data: LivetickerData,
        home_team_id: int,
        away_team_id: int,
    ) -> None:
        if not liveticker_data.players:
            return

        valid_team_ids = {
            home_team_id,
            away_team_id,
        }

        for external_id, player_data in (
            liveticker_data.players.items()
        ):
            normalized_external_id = (
                external_id.strip()
            )

            if not normalized_external_id:
                continue

            first_name = (
                MatchNotesBuilder
                .clean_import_text(
                    str(
                        player_data.get(
                            "first_name",
                            "",
                        )
                        or ""
                    )
                )
            )

            last_name = (
                MatchNotesBuilder
                .clean_import_text(
                    str(
                        player_data.get(
                            "last_name",
                            "",
                        )
                        or ""
                    )
                )
            )

            if not last_name:
                continue

            team_id = None

            team_external_id = str(
                player_data.get(
                    "team_external_id",
                    "",
                )
                or ""
            ).strip()

            if team_external_id:
                cache_key = (
                    match_id,
                    self._normalize_name(
                        team_external_id
                    ),
                )

                team_id = (
                    self._liveticker_team_cache.get(
                        cache_key
                    )
                )

                if team_id is None:
                    team_id = (
                        self._resolve_team_by_external_id(
                            external_id=team_external_id,
                            home_team_id=home_team_id,
                            away_team_id=away_team_id,
                        )
                    )

            if (
                team_id in valid_team_ids
                and first_name
                and last_name
            ):
                lineup_player_id = (
                    self._find_lineup_player_by_name(
                        match_id=match_id,
                        team_id=team_id,
                        player_name=(
                            f"{first_name} {last_name}"
                        ),
                    )
                )

                if lineup_player_id is not None:
                    self._link_external_id_to_player(
                        player_id=lineup_player_id,
                        external_id=(
                            normalized_external_id
                        ),
                    )
                    continue

            existing = (
                self.player_repository
                .get_by_external_id(
                    normalized_external_id
                )
            )

            if (
                team_id not in valid_team_ids
                and existing is not None
            ):
                existing_team_id = (
                    existing.get("team_id")
                )

                if (
                    existing_team_id is not None
                    and int(existing_team_id)
                    in valid_team_ids
                ):
                    team_id = int(
                        existing_team_id
                    )

            if team_id not in valid_team_ids:
                team_id = None

            self.player_repository.get_or_create(
                first_name=first_name,
                last_name=last_name,
                team_id=team_id,
                external_id=(
                    normalized_external_id
                ),
                commit=False,
            )

    def _prepare_liveticker_event(
        self,
        match_id: int,
        event: LivetickerEvent,
        team_id: int | None,
    ) -> dict | None:
        event_type_mapping = {
            "goal": "GOAL",
            "own_goal": "OWN_GOAL",
            "penalty_goal": "PENALTY_GOAL",
            "penalty_missed": "PENALTY_MISSED",
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
            match_id=match_id,
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
        match_id: int,
        event: LivetickerEvent,
        team_id: int | None,
    ) -> list[dict]:
        player_in_id = (
            self._get_or_create_player(
                match_id=match_id,
                player_name=event.player,
                external_id=event.player_id,
                team_id=team_id,
            )
        )

        player_out_id = (
            self._get_or_create_player(
                match_id=match_id,
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

    def _seed_liveticker_team_cache(
        self,
        match_id: int,
        liveticker_data: LivetickerData,
        home_team_id: int,
        away_team_id: int,
    ) -> None:
        # Die JSON-Quelle kennt Heim und Gast bereits positionssicher.
        # Deshalb zuerst deren Liveticker-Teamnamen direkt auf die
        # internen Match-Team-IDs legen. Das funktioniert auch bei 0:0-
        # Spielen, bei denen die bisherige Tor-Delta-Erkennung keinen
        # Cache aufbauen kann.
        home_liveticker_team = self._normalize_name(
            liveticker_data.home_team
        )
        away_liveticker_team = self._normalize_name(
            liveticker_data.away_team
        )

        if home_liveticker_team:
            self._liveticker_team_cache[
                (
                    match_id,
                    home_liveticker_team,
                )
            ] = home_team_id

        if away_liveticker_team:
            self._liveticker_team_cache[
                (
                    match_id,
                    away_liveticker_team,
                )
            ] = away_team_id

        team_external_ids = {
            self._normalize_name(
                event.team
            )
            for event in liveticker_data.events
            if self._normalize_name(
                event.team
            )
        }

        if not team_external_ids:
            return

        goal_types = {
            "goal",
            "own_goal",
            "penalty_goal",
        }

        goal_events = [
            event
            for event in liveticker_data.events
            if (
                event.event_type in goal_types
                and self._normalize_name(
                    event.team
                )
                and event.score_home is not None
                and event.score_away is not None
            )
        ]

        goal_events.sort(
            key=lambda event: (
                event.minute
                if event.minute is not None
                else 999,
                event.additional_time,
            )
        )

        previous_home = 0
        previous_away = 0

        for event in goal_events:
            external_team_id = (
                self._normalize_name(
                    event.team
                )
            )

            current_home = int(
                event.score_home
            )
            current_away = int(
                event.score_away
            )

            home_delta = (
                current_home
                - previous_home
            )
            away_delta = (
                current_away
                - previous_away
            )

            cache_key = (
                match_id,
                external_team_id,
            )

            if (
                home_delta > 0
                and away_delta <= 0
            ):
                self._liveticker_team_cache[
                    cache_key
                ] = home_team_id

            elif (
                away_delta > 0
                and home_delta <= 0
            ):
                self._liveticker_team_cache[
                    cache_key
                ] = away_team_id

            previous_home = max(
                previous_home,
                current_home,
            )
            previous_away = max(
                previous_away,
                current_away,
            )

        mapped_external_ids = {
            external_id: team_id
            for (
                cached_match_id,
                external_id,
            ), team_id
            in self._liveticker_team_cache.items()
            if cached_match_id == match_id
        }

        if (
            len(team_external_ids) == 2
            and len(mapped_external_ids) == 1
        ):
            mapped_external_id = next(
                iter(
                    mapped_external_ids
                )
            )

            mapped_team_id = (
                mapped_external_ids[
                    mapped_external_id
                ]
            )

            remaining_external_id = next(
                external_id
                for external_id
                in team_external_ids
                if external_id
                != mapped_external_id
            )

            remaining_team_id = (
                away_team_id
                if mapped_team_id
                == home_team_id
                else home_team_id
            )

            self._liveticker_team_cache[
                (
                    match_id,
                    remaining_external_id,
                )
            ] = remaining_team_id

    def _resolve_liveticker_team_id(
        self,
        match_id: int,
        event: LivetickerEvent,
        detail_data: MatchDetailData,
        home_team_id: int,
        away_team_id: int,
    ) -> int | None:
        event_team = self._normalize_name(
            event.team
        )

        home_name = self._normalize_name(
            detail_data.home_team
        )
        away_name = self._normalize_name(
            detail_data.away_team
        )

        if event_team:
            if event_team == home_name:
                return home_team_id

            if event_team == away_name:
                return away_team_id

            cache_key = (
                match_id,
                event_team,
            )

            cached_team_id = (
                self._liveticker_team_cache.get(
                    cache_key
                )
            )

            if cached_team_id is not None:
                return cached_team_id

            team_id = (
                self._resolve_team_by_external_id(
                    external_id=event.team,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                )
            )

            if team_id is not None:
                self._liveticker_team_cache[
                    cache_key
                ] = team_id

                return team_id

        team_id = (
            self._resolve_team_from_lineup(
                match_id=match_id,
                player_external_ids=(
                    event.player_id,
                    event.player_out_id,
                ),
                player_names=(
                    event.player,
                    event.player_out,
                ),
                home_team_id=home_team_id,
                away_team_id=away_team_id,
            )
        )

        if (
            team_id is not None
            and event_team
        ):
            self._liveticker_team_cache[
                (
                    match_id,
                    event_team,
                )
            ] = team_id

        return team_id

    def _resolve_team_by_external_id(
        self,
        external_id: str,
        home_team_id: int,
        away_team_id: int,
    ) -> int | None:
        normalized_external_id = (
            external_id.strip()
        )

        if not normalized_external_id:
            return None

        row = self.connection.execute(
            """
            SELECT team_id
            FROM teams
            WHERE external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        ).fetchone()

        if row is None:
            return None

        team_id = int(row[0])

        if team_id not in {
            home_team_id,
            away_team_id,
        }:
            return None

        return team_id

    def _resolve_team_from_lineup(
        self,
        match_id: int,
        player_external_ids: tuple[str, str],
        player_names: tuple[str, str],
        home_team_id: int,
        away_team_id: int,
    ) -> int | None:
        valid_team_ids = {
            home_team_id,
            away_team_id,
        }

        for external_id in player_external_ids:
            normalized_external_id = (
                external_id.strip()
            )

            if not normalized_external_id:
                continue

            row = self.connection.execute(
                """
                SELECT
                    lineups.team_id
                FROM lineups
                INNER JOIN players
                    ON players.player_id =
                       lineups.player_id
                WHERE
                    lineups.match_id = ?
                    AND players.external_id = ?
                LIMIT 1
                """,
                (
                    match_id,
                    normalized_external_id,
                ),
            ).fetchone()

            if row is None:
                continue

            team_id = int(row[0])

            if team_id in valid_team_ids:
                return team_id

        normalized_names = {
            self._normalize_name(name)
            for name in player_names
            if self._normalize_name(name)
        }

        if not normalized_names:
            return None

        rows = self.connection.execute(
            """
            SELECT
                lineups.team_id,
                players.first_name,
                players.last_name
            FROM lineups
            INNER JOIN players
                ON players.player_id =
                   lineups.player_id
            WHERE lineups.match_id = ?
            """,
            (match_id,),
        ).fetchall()

        for row in rows:
            team_id = int(row[0])

            if team_id not in valid_team_ids:
                continue

            first_name = str(
                row[1] or ""
            ).strip()
            last_name = str(
                row[2] or ""
            ).strip()

            full_name = self._normalize_name(
                " ".join(
                    part
                    for part in (
                        first_name,
                        last_name,
                    )
                    if part
                )
            )

            reverse_name = self._normalize_name(
                " ".join(
                    part
                    for part in (
                        last_name,
                        first_name,
                    )
                    if part
                )
            )

            if (
                full_name in normalized_names
                or reverse_name in normalized_names
            ):
                return team_id

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
        match_id: int | None = None,
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

        if (
            match_id is not None
            and team_id is not None
            and normalized_name
        ):
            lineup_player_id = (
                self._find_lineup_player_by_name(
                    match_id=match_id,
                    team_id=team_id,
                    player_name=normalized_name,
                )
            )

            if lineup_player_id is not None:
                if normalized_external_id:
                    self._link_external_id_to_player(
                        player_id=lineup_player_id,
                        external_id=(
                            normalized_external_id
                        ),
                    )

                return lineup_player_id

        if normalized_external_id:
            existing_by_external_id = (
                self.player_repository
                .get_by_external_id(
                    normalized_external_id
                )
            )

            if existing_by_external_id is not None:
                first_name, last_name = (
                    self._split_player_name(
                        normalized_name
                    )
                )

                return (
                    self.player_repository
                    .get_or_create(
                        first_name=(
                            first_name
                            or existing_by_external_id[
                                "first_name"
                            ]
                            or ""
                        ),
                        last_name=(
                            last_name
                            or existing_by_external_id[
                                "last_name"
                            ]
                            or (
                                "Unbekannt "
                                f"{normalized_external_id}"
                            )
                        ),
                        team_id=(
                            team_id
                            if team_id is not None
                            else existing_by_external_id[
                                "team_id"
                            ]
                        ),
                        external_id=(
                            normalized_external_id
                        ),
                        commit=False,
                    )
                )

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


    def _link_external_id_to_player(
        self,
        player_id: int,
        external_id: str,
    ) -> None:
        normalized_external_id = (
            external_id.strip()
        )

        if (
            player_id <= 0
            or not normalized_external_id
        ):
            return

        existing_row = self.connection.execute(
            """
            SELECT player_id
            FROM player_external_ids
            WHERE external_id = ?
            LIMIT 1
            """,
            (normalized_external_id,),
        ).fetchone()

        if existing_row is not None:
            existing_player_id = int(
                existing_row[0]
            )

            if existing_player_id == player_id:
                return

            target_player = self.connection.execute(
                """
                SELECT
                    player_id,
                    team_id,
                    first_name,
                    last_name
                FROM players
                WHERE player_id = ?
                LIMIT 1
                """,
                (player_id,),
            ).fetchone()

            existing_player = self.connection.execute(
                """
                SELECT
                    player_id,
                    team_id,
                    first_name,
                    last_name
                FROM players
                WHERE player_id = ?
                LIMIT 1
                """,
                (existing_player_id,),
            ).fetchone()

            if (
                target_player is None
                or existing_player is None
            ):
                raise ValueError(
                    "Spieler-Alias konnte nicht "
                    "sicher neu zugeordnet werden: "
                    f"{normalized_external_id}"
                )

            target_name = self._normalize_name(
                " ".join(
                    part
                    for part in (
                        str(
                            target_player[2]
                            or ""
                        ).strip(),
                        str(
                            target_player[3]
                            or ""
                        ).strip(),
                    )
                    if part
                )
            )

            existing_name = self._normalize_name(
                " ".join(
                    part
                    for part in (
                        str(
                            existing_player[2]
                            or ""
                        ).strip(),
                        str(
                            existing_player[3]
                            or ""
                        ).strip(),
                    )
                    if part
                )
            )

            target_team_id = target_player[1]
            existing_team_id = existing_player[1]

            same_team = (
                target_team_id is not None
                and existing_team_id is not None
                and int(target_team_id)
                == int(existing_team_id)
            )

            existing_team_unknown = (
                existing_team_id is None
                and target_team_id is not None
            )

            same_name = (
                bool(target_name)
                and target_name == existing_name
            )

            if not (
                same_name
                and (
                    same_team
                    or existing_team_unknown
                )
            ):
                raise ValueError(
                    "Liveticker-Spieler-ID ist bereits "
                    "einem anderen Spieler zugeordnet "
                    "und die Identität ist nicht "
                    "eindeutig identisch: "
                    f"{normalized_external_id}"
                )

            # Alter Importbestand: Derselbe Spieler wurde
            # bereits doppelt angelegt, weil Lineup und
            # Liveticker unterschiedliche External-IDs
            # geliefert haben. In diesem eindeutigen Fall
            # darf der Liveticker-Alias auf den Lineup-
            # Spieler umgehängt werden.
            self.connection.execute(
                """
                UPDATE player_external_ids
                SET
                    player_id = ?,
                    source = 'liveticker'
                WHERE external_id = ?
                """,
                (
                    player_id,
                    normalized_external_id,
                ),
            )

            # Die alte Dublette darf die External-ID nicht
            # mehr als primäre ID behalten, da
            # get_by_external_id() sonst weiterhin zuerst
            # diesen Datensatz finden würde.
            self.connection.execute(
                """
                UPDATE players
                SET external_id = NULL
                WHERE
                    player_id = ?
                    AND external_id = ?
                """,
                (
                    existing_player_id,
                    normalized_external_id,
                ),
            )

            if (
                existing_team_id is None
                and target_team_id is not None
            ):
                self.connection.execute(
                    """
                    UPDATE players
                    SET team_id = ?
                    WHERE player_id = ?
                    """,
                    (
                        int(target_team_id),
                        existing_player_id,
                    ),
                )

            return

        self.connection.execute(
            """
            INSERT INTO player_external_ids (
                player_id,
                external_id,
                source
            )
            VALUES (?, ?, ?)
            """,
            (
                player_id,
                normalized_external_id,
                "liveticker",
            ),
        )

        self.connection.execute(
            """
            UPDATE players
            SET external_id = ?
            WHERE
                player_id = ?
                AND (
                    external_id IS NULL
                    OR external_id = ''
                )
            """,
            (
                normalized_external_id,
                player_id,
            ),
        )

    def _find_lineup_player_by_name(
        self,
        match_id: int,
        team_id: int,
        player_name: str,
    ) -> int | None:
        target = self._normalize_name(
            player_name
        )

        if not target:
            return None

        rows = self.connection.execute(
            """
            SELECT
                players.player_id,
                players.first_name,
                players.last_name
            FROM lineups
            INNER JOIN players
                ON players.player_id =
                   lineups.player_id
            WHERE
                lineups.match_id = ?
                AND lineups.team_id = ?
            """,
            (
                match_id,
                team_id,
            ),
        ).fetchall()

        exact_matches: list[int] = []
        relaxed_matches: list[int] = []

        for row in rows:
            player_id = int(
                row[0]
            )

            first_name = str(
                row[1] or ""
            ).strip()

            last_name = str(
                row[2] or ""
            ).strip()

            full_name = self._normalize_name(
                " ".join(
                    part
                    for part in (
                        first_name,
                        last_name,
                    )
                    if part
                )
            )

            reverse_name = self._normalize_name(
                " ".join(
                    part
                    for part in (
                        last_name,
                        first_name,
                    )
                    if part
                )
            )

            normalized_first = (
                self._normalize_name(
                    first_name
                )
            )
            normalized_last = (
                self._normalize_name(
                    last_name
                )
            )

            if target in {
                full_name,
                reverse_name,
            }:
                exact_matches.append(
                    player_id
                )
                continue

            if (
                target
                and (
                    target == normalized_first
                    or target == normalized_last
                )
            ):
                relaxed_matches.append(
                    player_id
                )
                continue

            shorter = (
                full_name
                if len(full_name) <= len(target)
                else target
            )

            longer = (
                target
                if len(target) >= len(full_name)
                else full_name
            )

            shorter_tokens = (
                shorter.split()
            )

            if (
                len(shorter_tokens) >= 2
                and len(shorter) >= 8
                and longer.startswith(
                    shorter + " "
                )
            ):
                relaxed_matches.append(
                    player_id
                )

        if len(exact_matches) == 1:
            return exact_matches[0]

        if len(relaxed_matches) == 1:
            return relaxed_matches[0]

        return None

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