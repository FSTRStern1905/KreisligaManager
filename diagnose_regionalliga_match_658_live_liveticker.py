from __future__ import annotations

import json
from pathlib import Path

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.liveticker_loader import (
    LivetickerLoader,
)


MATCH_EXTERNAL_ID = "02TNUVBCCK000000VS5489BUVSSD35NB"

SOURCE_URL = (
    "https://www.fussball.de/spiel/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)

DEBUG_JSON = Path(
    "debug/liveticker/json"
) / f"{MATCH_EXTERNAL_ID}.json"


def separator(title: str) -> None:
    print()
    print("=" * 110)
    print(title)
    print("=" * 110)


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 658 / LIVE-LIVETICKER-DIAGNOSE "
        "FÜR DAS FEHLENDE 6:0"
    )
    print("=" * 110)
    print(f"Match-ID: {MATCH_EXTERNAL_ID}")
    print("Keine Datenbankänderung.")

    browser = FussballDeBrowser()

    try:
        browser.start(
            headless=True,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht erstellt werden."
            )

        loader = LivetickerLoader()

        separator("LIVETICKER LADEN")

        data = loader.load(
            page=browser.page,
            source_url=SOURCE_URL,
            match_external_id=MATCH_EXTERNAL_ID,
        )

        print(
            f"Ermittelte ticker_id: "
            f"{getattr(loader, 'last_ticker_id', None)}"
        )

        if data is None:
            print(
                "LivetickerLoader lieferte keine "
                "importierbaren Daten."
            )
        else:
            print(
                f"Parsed Events: "
                f"{len(data.events)}"
            )

            separator("PARSED EVENTS")

            for event in data.events:
                print(
                    {
                        "type": event.event_type,
                        "minute": event.minute,
                        "player": event.player,
                        "player_id": event.player_id,
                        "team": event.team,
                        "score": event.score,
                        "description": event.description,
                    }
                )

            goal_events = [
                event
                for event in data.events
                if event.event_type in {
                    "goal",
                    "penalty_goal",
                    "own_goal",
                }
            ]

            separator("PARSED TOR-EVENTS")

            if not goal_events:
                print("(keine)")
            else:
                for event in goal_events:
                    print(
                        {
                            "type": event.event_type,
                            "minute": event.minute,
                            "player": event.player,
                            "team": event.team,
                            "score": event.score,
                            "description": event.description,
                        }
                    )

            print()
            print(
                f"Tor-Events parsed: "
                f"{len(goal_events)}"
            )

        separator("GESPEICHERTES DEBUG-JSON")

        if not DEBUG_JSON.exists():
            print(
                f"Nicht gefunden: {DEBUG_JSON}"
            )
        else:
            raw = json.loads(
                DEBUG_JSON.read_text(
                    encoding="utf-8",
                )
            )

            print(
                f"Datei: {DEBUG_JSON}"
            )

            raw_events = raw.get(
                "events",
                [],
            )

            print(
                f"Raw Events: "
                f"{len(raw_events)}"
            )

            separator("RAW EVENTS MIT SPIELSTAND / TORBEZUG")

            interesting = []

            for event in raw_events:
                text = json.dumps(
                    event,
                    ensure_ascii=False,
                ).lower()

                if (
                    "goal" in text
                    or "tor" in text
                    or "6:0" in text
                    or "5:0" in text
                ):
                    interesting.append(
                        event
                    )

            if not interesting:
                print("(keine)")
            else:
                for event in interesting:
                    print(
                        json.dumps(
                            event,
                            ensure_ascii=False,
                            indent=2,
                        )
                    )

            raw_text = json.dumps(
                raw,
                ensure_ascii=False,
            )

            separator("SPIELSTAND-SUCHE IM RAW-JSON")

            for needle in (
                "6:0",
                "6 : 0",
                "5:0",
                "5 : 0",
            ):
                print(
                    f"{needle!r}: "
                    f"{raw_text.count(needle)}"
                )

        separator("BEFUND-HILFE")
        print(
            "Wenn das RAW-JSON bereits nur 5 Tor-Events "
            "und keinen 6:0-Eintrag enthält, ist die "
            "Abweichung quellseitig."
        )
        print(
            "Wenn RAW-JSON ein 6:0 enthält, aber PARSED "
            "TOR-EVENTS nur 5 zeigt, liegt der Fehler "
            "im LivetickerParser."
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()
