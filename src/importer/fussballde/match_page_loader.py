from __future__ import annotations

from pathlib import Path
from typing import Any


class MatchPageLoader:
    """
    Lädt die Match-Detailseite und speichert optional
    den HTML-Stand zur Fehlersuche.

    Zuständig für:
    - Seitenaufruf
    - Load-State
    - kurze Wartezeit
    - HTML auslesen
    - Debug-HTML speichern
    """

    DEBUG_PATH = Path(
        "debug/html/matches"
    )

    def load(
        self,
        page: Any,
        source_url: str,
    ) -> str:
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

        self.save_debug_html(
            html=html,
            source_url=normalized_url,
        )

        return html

    def save_debug_html(
        self,
        html: str,
        source_url: str,
    ) -> Path:
        match_id = self.extract_match_id_from_url(
            source_url
        )

        if not match_id:
            match_id = "unknown_match"

        self.DEBUG_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = (
            self.DEBUG_PATH
            / f"{match_id}.html"
        )

        file_path.write_text(
            html,
            encoding="utf-8",
        )

        return file_path

    @staticmethod
    def extract_match_id_from_url(
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