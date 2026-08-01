from __future__ import annotations

import re

from src.validator.match_snapshot import (
    MatchSnapshot,
    SnapshotEvent,
    SnapshotPlayer,
)
from src.validator.snapshot_loader import (
    LoadedMatchData,
    SnapshotLoader,
)


class SnapshotBuilder:
    """
    Erstellt aus den geladenen Datenbankdaten einen
    vollständig typisierten MatchSnapshot.

    Der Builder kennt kein SQL und greift ausschließlich
    über den SnapshotLoader auf Daten zu.
    """

    EVENT_TYPE_MAPPING = {
        "GOAL": "goal",
        "PENALTY_GOAL": "goal",
        "OWN_GOAL": "own_goal",
        "YELLOW_CARD": "yellow_card",
        "YELLOW_RED_CARD": "second_yellow_card",
        "RED_CARD": "red_card",
        "PENALTY_MISSED": "penalty_missed",
        "SUBSTITUTION_IN": "substitution",
        "SUBSTITUTION_OUT": "substitution",
    }

    def __init__(
        self,
        loader: SnapshotLoader,
    ) -> None:
        self.loader = loader

    def build_by_external_id(
        self,
        external_id: str,
    ) -> MatchSnapshot:
        normalized_external_id = external_id.strip()

        if not normalized_external_id:
            raise ValueError(
                "Die externe Spiel-ID darf nicht leer sein."
            )

        loaded_data = self.loader.load_by_external_id(
            normalized_external_id
        )

        return self.build(
            loaded_data
        )

    def build(
        self,
        loaded_data: LoadedMatchData,
    ) -> MatchSnapshot:
        match = loaded_data.match

        if match.match_id is None:
            raise ValueError(
                "Das geladene Spiel besitzt keine interne ID."
            )

        halftime_home, halftime_away = (
            self._extract_halftime_result(
                match.notes
            )
        )

        snapshot = MatchSnapshot(
            match_id=match.external_id or str(
                match.match_id
            ),
            home_team=match.home_team_name,
            away_team=match.away_team_name,
            home_goals=match.home_goals,
            away_goals=match.away_goals,
            halftime_home=halftime_home,
            halftime_away=halftime_away,
            stadium=self._build_stadium_name(
                loaded_data.stadium
            ),
            referee=self._build_referee_name(
                loaded_data.referee
            ),
            attendance=match.attendance,
        )

        snapshot.home_players = (
            self._build_players(
                team_id=int(match.home_team_id),
                team_name=match.home_team_name,
                loaded_data=loaded_data,
            )
        )

        snapshot.away_players = (
            self._build_players(
                team_id=int(match.away_team_id),
                team_name=match.away_team_name,
                loaded_data=loaded_data,
            )
        )

        snapshot.events = self._build_events(
            loaded_data=loaded_data,
            home_team_id=int(
                match.home_team_id
            ),
            away_team_id=int(
                match.away_team_id
            ),
            home_team_name=match.home_team_name,
            away_team_name=match.away_team_name,
        )

        return snapshot

    def _build_players(
        self,
        team_id: int,
        team_name: str,
        loaded_data: LoadedMatchData,
    ) -> list[SnapshotPlayer]:
        if team_id <= 0:
            raise ValueError(
                "Ungültige Mannschafts-ID."
            )

        team_players = self._get_team_players(
            team_id=team_id,
            loaded_data=loaded_data,
        )

        player_lookup = {
            int(player["player_id"]): player
            for player in team_players
            if player.get("player_id") is not None
        }

        players: list[SnapshotPlayer] = []

        for lineup in loaded_data.lineups:
            if int(lineup["team_id"]) != team_id:
                continue

            player_id = int(
                lineup["player_id"]
            )

            player = player_lookup.get(
                player_id
            )

            if player is None:
                continue

            players.append(
                SnapshotPlayer(
                    player_id=str(
                        player.get(
                            "external_id",
                            "",
                        )
                        or player_id
                    ),
                    name=self._build_player_name(
                        player
                    ),
                    team=team_name,
                    number=self._get_shirt_number(
                        lineup=lineup,
                        player=player,
                    ),
                    position=str(
                        lineup.get(
                            "position",
                            "",
                        )
                        or player.get(
                            "position",
                            "",
                        )
                        or ""
                    ),
                    is_starting=bool(
                        lineup.get(
                            "is_starting",
                            False,
                        )
                    ),
                    is_captain=False,
                )
            )

        players.sort(
            key=lambda player: (
                not player.is_starting,
                (
                    player.number
                    if player.number is not None
                    else 999
                ),
                player.name.casefold(),
            )
        )

        return players

    def _build_events(
        self,
        loaded_data: LoadedMatchData,
        home_team_id: int,
        away_team_id: int,
        home_team_name: str,
        away_team_name: str,
    ) -> list[SnapshotEvent]:
        player_lookup = self._build_player_lookup(
            loaded_data
        )

        events: list[SnapshotEvent] = []
        processed_event_ids: set[int] = set()

        database_events = loaded_data.events

        for event in database_events:
            event_id = int(
                event["event_id"]
            )

            if event_id in processed_event_ids:
                continue

            event_type_code = str(
                event.get(
                    "event_type_code",
                    "",
                )
                or ""
            ).upper()

            if event_type_code in {
                "SUBSTITUTION_IN",
                "SUBSTITUTION_OUT",
            }:
                substitution = (
                    self._build_substitution_event(
                        event=event,
                        all_events=database_events,
                        player_lookup=player_lookup,
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        home_team_name=home_team_name,
                        away_team_name=away_team_name,
                        processed_event_ids=(
                            processed_event_ids
                        ),
                    )
                )

                events.append(
                    substitution
                )

                continue

            processed_event_ids.add(
                event_id
            )

            event_type = self.EVENT_TYPE_MAPPING.get(
                event_type_code,
                event_type_code.casefold(),
            )

            player = self._get_player(
                event.get("player_id"),
                player_lookup,
            )

            home_goals, away_goals = (
                self._extract_event_score(
                    str(
                        event.get(
                            "value",
                            "",
                        )
                        or ""
                    )
                )
            )

            events.append(
                SnapshotEvent(
                    minute=event.get(
                        "minute"
                    ),
                    additional_time=(
                        self._extract_additional_time(
                            str(
                                event.get(
                                    "value",
                                    "",
                                )
                                or ""
                            )
                        )
                    ),
                    event_type=event_type,
                    team=self._resolve_team_name(
                        team_id=event.get(
                            "team_id"
                        ),
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        home_team_name=(
                            home_team_name
                        ),
                        away_team_name=(
                            away_team_name
                        ),
                    ),
                    player=self._build_player_name(
                        player
                    ),
                    player_id=self._get_external_player_id(
                        player
                    ),
                    home_goals=home_goals,
                    away_goals=away_goals,
                    value=str(
                        event.get(
                            "value",
                            "",
                        )
                        or ""
                    ),
                    description=str(
                        event.get(
                            "notes",
                            "",
                        )
                        or ""
                    ),
                )
            )

        events.sort(
            key=lambda event: (
                (
                    event.minute
                    if event.minute is not None
                    else 999
                ),
                event.additional_time,
                event.event_type,
                event.player.casefold(),
            )
        )

        return events

    def _build_substitution_event(
        self,
        event: dict,
        all_events: list[dict],
        player_lookup: dict[int, dict],
        home_team_id: int,
        away_team_id: int,
        home_team_name: str,
        away_team_name: str,
        processed_event_ids: set[int],
    ) -> SnapshotEvent:
        event_id = int(
            event["event_id"]
        )

        processed_event_ids.add(
            event_id
        )

        event_type_code = str(
            event.get(
                "event_type_code",
                "",
            )
            or ""
        ).upper()

        player_id = event.get(
            "player_id"
        )

        related_player_id = event.get(
            "related_player_id"
        )

        if event_type_code == "SUBSTITUTION_IN":
            player_in_id = player_id
            player_out_id = related_player_id
        else:
            player_in_id = related_player_id
            player_out_id = player_id

        matching_event = self._find_matching_substitution(
            source_event=event,
            all_events=all_events,
        )

        if matching_event is not None:
            processed_event_ids.add(
                int(
                    matching_event["event_id"]
                )
            )

        player_in = self._get_player(
            player_in_id,
            player_lookup,
        )

        player_out = self._get_player(
            player_out_id,
            player_lookup,
        )

        value = str(
            event.get(
                "value",
                "",
            )
            or ""
        )

        return SnapshotEvent(
            minute=event.get(
                "minute"
            ),
            additional_time=(
                self._extract_additional_time(
                    value
                )
            ),
            event_type="substitution",
            team=self._resolve_team_name(
                team_id=event.get(
                    "team_id"
                ),
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=home_team_name,
                away_team_name=away_team_name,
            ),
            player=self._build_player_name(
                player_in
            ),
            player_id=self._get_external_player_id(
                player_in
            ),
            player_out=self._build_player_name(
                player_out
            ),
            player_out_id=(
                self._get_external_player_id(
                    player_out
                )
            ),
            value="substitution",
            description=str(
                event.get(
                    "notes",
                    "",
                )
                or ""
            ),
        )

    @staticmethod
    def _find_matching_substitution(
        source_event: dict,
        all_events: list[dict],
    ) -> dict | None:
        source_code = str(
            source_event.get(
                "event_type_code",
                "",
            )
            or ""
        ).upper()

        expected_code = (
            "SUBSTITUTION_OUT"
            if source_code == "SUBSTITUTION_IN"
            else "SUBSTITUTION_IN"
        )

        for event in all_events:
            if (
                event.get("event_id")
                == source_event.get(
                    "event_id"
                )
            ):
                continue

            event_code = str(
                event.get(
                    "event_type_code",
                    "",
                )
                or ""
            ).upper()

            if event_code != expected_code:
                continue

            if (
                event.get("match_id")
                != source_event.get(
                    "match_id"
                )
            ):
                continue

            if (
                event.get("team_id")
                != source_event.get(
                    "team_id"
                )
            ):
                continue

            if (
                event.get("minute")
                != source_event.get(
                    "minute"
                )
            ):
                continue

            source_player = source_event.get(
                "player_id"
            )
            source_related = source_event.get(
                "related_player_id"
            )

            event_player = event.get(
                "player_id"
            )
            event_related = event.get(
                "related_player_id"
            )

            if (
                source_player == event_related
                and source_related == event_player
            ):
                return event

        return None

    @staticmethod
    def _get_team_players(
        team_id: int,
        loaded_data: LoadedMatchData,
    ) -> list[dict]:
        match = loaded_data.match

        if team_id == int(
            match.home_team_id
        ):
            return loaded_data.home_players

        if team_id == int(
            match.away_team_id
        ):
            return loaded_data.away_players

        return []

    @staticmethod
    def _build_player_lookup(
        loaded_data: LoadedMatchData,
    ) -> dict[int, dict]:
        players = (
            loaded_data.home_players
            + loaded_data.away_players
        )

        return {
            int(player["player_id"]): player
            for player in players
            if player.get(
                "player_id"
            ) is not None
        }

    @staticmethod
    def _get_player(
        player_id: int | None,
        player_lookup: dict[int, dict],
    ) -> dict | None:
        if player_id is None:
            return None

        return player_lookup.get(
            int(player_id)
        )

    @staticmethod
    def _build_player_name(
        player: dict | None,
    ) -> str:
        if player is None:
            return ""

        first_name = str(
            player.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            player.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        return " ".join(
            value
            for value in (
                first_name,
                last_name,
            )
            if value
        )

    @staticmethod
    def _get_external_player_id(
        player: dict | None,
    ) -> str:
        if player is None:
            return ""

        external_id = str(
            player.get(
                "external_id",
                "",
            )
            or ""
        ).strip()

        if external_id:
            return external_id

        player_id = player.get(
            "player_id"
        )

        if player_id is None:
            return ""

        return str(
            player_id
        )

    @staticmethod
    def _get_shirt_number(
        lineup: dict,
        player: dict,
    ) -> int | None:
        lineup_number = lineup.get(
            "shirt_number"
        )

        if lineup_number is not None:
            return int(
                lineup_number
            )

        player_number = player.get(
            "shirt_number"
        )

        if player_number is None:
            return None

        return int(
            player_number
        )

    @staticmethod
    def _build_referee_name(
        referee: dict | None,
    ) -> str:
        if referee is None:
            return ""

        first_name = str(
            referee.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            referee.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        return " ".join(
            value
            for value in (
                first_name,
                last_name,
            )
            if value
        )

    @staticmethod
    def _build_stadium_name(
        stadium: dict | None,
    ) -> str:
        if stadium is None:
            return ""

        return str(
            stadium.get(
                "name",
                "",
            )
            or ""
        ).strip()

    @staticmethod
    def _resolve_team_name(
        team_id: int | None,
        home_team_id: int,
        away_team_id: int,
        home_team_name: str,
        away_team_name: str,
    ) -> str:
        if team_id is None:
            return ""

        normalized_team_id = int(
            team_id
        )

        if normalized_team_id == home_team_id:
            return home_team_name

        if normalized_team_id == away_team_id:
            return away_team_name

        return ""

    @staticmethod
    def _extract_halftime_result(
        notes: str,
    ) -> tuple[int | None, int | None]:
        normalized_notes = notes or ""

        match = re.search(
            r"Halbzeit\s*:\s*(\d+)\s*:\s*(\d+)",
            normalized_notes,
            re.IGNORECASE,
        )

        if match is None:
            return None, None

        return (
            int(match.group(1)),
            int(match.group(2)),
        )

    @staticmethod
    def _extract_event_score(
        value: str,
    ) -> tuple[int | None, int | None]:
        match = re.search(
            r"(?<!\d)(\d+)\s*:\s*(\d+)(?!\d)",
            value,
        )

        if match is None:
            return None, None

        return (
            int(match.group(1)),
            int(match.group(2)),
        )

    @staticmethod
    def _extract_additional_time(
        value: str,
    ) -> int:
        match = re.search(
            r"Nachspielzeit\s*:\s*(\d+)",
            value,
            re.IGNORECASE,
        )

        if match is None:
            return 0

        return int(
            match.group(1)
        )