from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.importer.fussballde.liveticker_data import (
    LivetickerData,
)
from src.importer.fussballde.liveticker_json_parser import (
    LivetickerJsonParser,
)


class LivetickerLoader:
    """
    Lädt und parst die Liveticker-Daten eines Spiels.

    Zuständig für:
    - Liveticker-URL erzeugen
    - Netzwerkantworten beobachten
    - passenden JSON-Payload auswählen
    - Debug-JSON speichern
    - Liveticker-Daten parsen
    - Importierbarkeit prüfen
    """

    DEBUG_PATH = Path(
        "debug/liveticker/json"
    )

    IMPORTABLE_EVENT_TYPES = {
        "goal",
        "yellow_card",
        "yellow_red_card",
        "red_card",
        "substitution",
    }

    def __init__(self) -> None:
        self.parser = LivetickerJsonParser()

    def load(
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

        liveticker_url = self.build_url(
            source_url
        )

        try:
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

        self.save_debug_json(
            match_external_id=(
                match_external_id
            ),
            payload=payload,
        )

        try:
            data = self.parser.parse(
                payload=payload,
                source_url=liveticker_url,
            )
        except Exception:
            return None

        if not self.has_importable_events(
            data
        ):
            return None

        return data

    @staticmethod
    def build_url(
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

    def save_debug_json(
        self,
        match_external_id: str,
        payload: dict,
    ) -> Path:
        self.DEBUG_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_match_id = (
            match_external_id.strip()
            or "unknown_match"
        )

        file_path = (
            self.DEBUG_PATH
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

    @classmethod
    def has_importable_events(
        cls,
        data: LivetickerData,
    ) -> bool:
        return any(
            event.event_type
            in cls.IMPORTABLE_EVENT_TYPES
            for event in data.events
        )