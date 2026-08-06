from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.importer.fussballde.liveticker_data import (
    LivetickerData,
    LivetickerEvent,
)


class LivetickerJsonParser:
    TYPE_GOAL = 1
    TYPE_YELLOW_CARD = 2
    TYPE_SUBSTITUTION = 4
    TYPE_CORNER = 5
    TYPE_OFFSIDE = 6
    TYPE_KICKOFF = 28
    TYPE_FULLTIME = 29

    EVENT_TYPE_BY_ID = {
        TYPE_GOAL: "goal",
        TYPE_YELLOW_CARD: "yellow_card",
        TYPE_SUBSTITUTION: "substitution",
        TYPE_CORNER: "corner",
        TYPE_OFFSIDE: "offside",
        TYPE_KICKOFF: "kickoff",
        TYPE_FULLTIME: "fulltime",
    }

    def parse(
        self,
        payload: str | bytes | dict[str, Any],
        source_url: str = "",
    ) -> LivetickerData:
        raw_data = self._normalize_payload(
            payload
        )

        match_id = str(
            raw_data.get(
                "matchId",
                "",
            )
            or raw_data.get(
                "id",
                "",
            )
            or ""
        ).strip()

        home_team = self._parse_team(
            raw_data.get(
                "home_team"
            )
        )

        away_team = self._parse_team(
            raw_data.get(
                "guest_team"
            )
        )

        member_index = {
            **home_team["members"],
            **away_team["members"],
        }

        team_index = {
            home_team["id"]: home_team["name"],
            away_team["id"]: away_team["name"],
        }

        (
            home_score,
            away_score,
        ) = self._parse_score(
            raw_data.get(
                "score"
            )
        )

        data = LivetickerData(
            source_url=source_url,
            match_id=match_id,
            page_title=(
                f"{home_team['name']} - "
                f"{away_team['name']}"
            ).strip(" -"),
            home_team=home_team["name"],
            away_team=away_team["name"],
            home_score=home_score,
            away_score=away_score,
            ticker_available=bool(
                raw_data.get(
                    "liveticker_enabled",
                    False,
                )
            ),
            source_type="fussballde_json",
        )

        raw_events = raw_data.get(
            "events",
            [],
        )

        if not isinstance(
            raw_events,
            list,
        ):
            data.warnings.append(
                "Das Feld 'events' besitzt "
                "kein gültiges Listenformat."
            )
            raw_events = []

        for raw_event in raw_events:
            if not isinstance(
                raw_event,
                dict,
            ):
                continue

            event = self._parse_event(
                raw_event=raw_event,
                team_index=team_index,
                member_index=member_index,
            )

            if event is not None:
                data.events.append(
                    event
                )

        data.events.sort(
            key=self._event_sort_key
        )

        if not data.ticker_available:
            data.warnings.append(
                "Der Liveticker ist laut Quelle "
                "nicht aktiviert."
            )

        if not data.events:
            data.warnings.append(
                "Die Liveticker-Antwort enthält "
                "keine Ereignisse."
            )

        unknown_type_ids = sorted(
            {
                int(
                    event.raw_data.get(
                        "type_id"
                    )
                )
                for event in data.events
                if (
                    event.event_type == "unknown"
                    and self._is_integer(
                        event.raw_data.get(
                            "type_id"
                        )
                    )
                )
            }
        )

        if unknown_type_ids:
            data.warnings.append(
                "Unbekannte Liveticker-Type-IDs: "
                + ", ".join(
                    str(type_id)
                    for type_id in unknown_type_ids
                )
            )

        return data

    def parse_file(
        self,
        path: str | Path,
        source_url: str = "",
    ) -> LivetickerData:
        file_path = Path(
            path
        )

        if not file_path.exists():
            raise FileNotFoundError(
                f"JSON-Datei nicht gefunden: "
                f"{file_path}"
            )

        return self.parse(
            payload=file_path.read_bytes(),
            source_url=source_url,
        )

    def _parse_event(
        self,
        raw_event: dict[str, Any],
        team_index: dict[str, str],
        member_index: dict[str, dict[str, Any]],
    ) -> LivetickerEvent | None:
        type_id = self._to_integer(
            raw_event.get(
                "type_id"
            )
        )

        if type_id is None:
            return None

        member_id = str(
            raw_event.get(
                "member_id",
                "",
            )
            or ""
        ).strip()

        member2_id = str(
            raw_event.get(
                "member2_id",
                "",
            )
            or ""
        ).strip()

        team_id = str(
            raw_event.get(
                "team_id",
                "",
            )
            or ""
        ).strip()

        player_data = member_index.get(
            member_id,
            {},
        )

        second_player_data = member_index.get(
            member2_id,
            {},
        )

        player_name = self._member_name(
            player_data
        )

        second_player_name = self._member_name(
            second_player_data
        )

        event_type = self.EVENT_TYPE_BY_ID.get(
            type_id,
            "unknown",
        )

        minute = self._to_integer(
            raw_event.get(
                "minute"
            )
        )

        additional_time = (
            self._to_integer(
                raw_event.get(
                    "minute_additional"
                )
            )
            or 0
        )

        (
            score_home,
            score_away,
        ) = self._parse_score(
            raw_event.get(
                "score"
            )
        )

        description = str(
            raw_event.get(
                "description",
                "",
            )
            or ""
        ).strip()

        comment = str(
            raw_event.get(
                "comment",
                "",
            )
            or ""
        ).strip()

        full_description = description

        if comment:
            full_description = (
                f"{description} – {comment}"
                if description
                else comment
            )

        return LivetickerEvent(
            minute=minute,
            additional_time=additional_time,
            event_type=event_type,
            team=team_index.get(
                team_id,
                "",
            ),
            player=player_name,
            player_id=self._member_player_id(
                player_data,
                fallback=member_id,
            ),
            player_out=(
                second_player_name
                if type_id == self.TYPE_SUBSTITUTION
                else ""
            ),
            player_out_id=(
                self._member_player_id(
                    second_player_data,
                    fallback=member2_id,
                )
                if type_id == self.TYPE_SUBSTITUTION
                else ""
            ),
            score_home=score_home,
            score_away=score_away,
            title=description,
            description=full_description,
            source_event_id=str(
                raw_event.get(
                    "id",
                    "",
                )
                or ""
            ).strip(),
            raw_data={
                **raw_event,
                "resolved_team_name": (
                    team_index.get(
                        team_id,
                        "",
                    )
                ),
                "resolved_member_name": (
                    player_name
                ),
                "resolved_member2_name": (
                    second_player_name
                ),
            },
        )

    @staticmethod
    def _parse_team(
        raw_team: Any,
    ) -> dict[str, Any]:
        if not isinstance(
            raw_team,
            dict,
        ):
            return {
                "id": "",
                "name": "",
                "members": {},
            }

        raw_members = raw_team.get(
            "members",
            {},
        )

        members: dict[
            str,
            dict[str, Any],
        ] = {}

        if isinstance(
            raw_members,
            dict,
        ):
            for member_key, member_value in (
                raw_members.items()
            ):
                if not isinstance(
                    member_value,
                    dict,
                ):
                    continue

                member_id = str(
                    member_value.get(
                        "id",
                        member_key,
                    )
                    or member_key
                    or ""
                ).strip()

                if member_id:
                    members[member_id] = dict(
                        member_value
                    )

        elif isinstance(
            raw_members,
            list,
        ):
            for member_value in raw_members:
                if not isinstance(
                    member_value,
                    dict,
                ):
                    continue

                member_id = str(
                    member_value.get(
                        "id",
                        "",
                    )
                    or ""
                ).strip()

                if member_id:
                    members[member_id] = dict(
                        member_value
                    )

        return {
            "id": str(
                raw_team.get(
                    "id",
                    "",
                )
                or ""
            ).strip(),
            "name": str(
                raw_team.get(
                    "name",
                    "",
                )
                or ""
            ).strip(),
            "members": members,
        }

    @staticmethod
    def _member_name(
        member: dict[str, Any],
    ) -> str:
        first_name = str(
            member.get(
                "firstname",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            member.get(
                "name",
                "",
            )
            or ""
        ).strip()

        return " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        )

    @staticmethod
    def _member_player_id(
        member: dict[str, Any],
        fallback: str,
    ) -> str:
        return str(
            member.get(
                "player_id",
                "",
            )
            or member.get(
                "id",
                "",
            )
            or fallback
            or ""
        ).strip()

    @staticmethod
    def _parse_score(
        value: Any,
    ) -> tuple[
        int | None,
        int | None,
    ]:
        if isinstance(
            value,
            dict,
        ):
            home = LivetickerJsonParser._to_integer(
                value.get(
                    "home"
                )
                or value.get(
                    "homeScore"
                )
            )
            away = LivetickerJsonParser._to_integer(
                value.get(
                    "away"
                )
                or value.get(
                    "awayScore"
                )
            )
            return home, away

        if not isinstance(
            value,
            str,
        ):
            return None, None

        match = re.search(
            r"(?<!\d)(\d+)\s*[:\-]\s*(\d+)(?!\d)",
            value,
        )

        if not match:
            return None, None

        return (
            int(match.group(1)),
            int(match.group(2)),
        )

    @staticmethod
    def _event_sort_key(
        event: LivetickerEvent,
    ) -> tuple[int, int, str]:
        return (
            event.minute
            if event.minute is not None
            else 999,
            event.additional_time,
            event.source_event_id,
        )

    @staticmethod
    def _normalize_payload(
        payload: str | bytes | dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(
            payload,
            dict,
        ):
            return payload

        if isinstance(
            payload,
            bytes,
        ):
            payload = payload.decode(
                "utf-8",
                errors="replace",
            )

        if isinstance(
            payload,
            str,
        ):
            parsed = json.loads(
                payload
            )

            if not isinstance(
                parsed,
                dict,
            ):
                raise ValueError(
                    "Die Liveticker-Antwort muss "
                    "ein JSON-Objekt enthalten."
                )

            return parsed

        raise TypeError(
            "Payload muss dict, str oder bytes sein."
        )

    @staticmethod
    def _to_integer(
        value: Any,
    ) -> int | None:
        if isinstance(
            value,
            bool,
        ):
            return None

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
            normalized = value.strip()

            if normalized.lstrip(
                "-"
            ).isdigit():
                return int(
                    normalized
                )

        return None

    @staticmethod
    def _is_integer(
        value: Any,
    ) -> bool:
        return (
            LivetickerJsonParser._to_integer(
                value
            )
            is not None
        )