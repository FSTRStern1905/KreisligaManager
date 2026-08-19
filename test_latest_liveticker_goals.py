from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEBUG_DIR = Path("debug/liveticker/json")
MAX_FILES = 10


def get_events(data: Any) -> list[dict]:
    if isinstance(data, dict):
        events = data.get("events")
        if isinstance(events, list):
            return [
                event
                for event in events
                if isinstance(event, dict)
            ]

    return []


def is_goal_event(event: dict) -> bool:
    return event.get("type_id") in {
        1,    # Tor
        12,   # Eigentor
        100,  # Strafstoß-Tor
    }


def main() -> None:
    if not DEBUG_DIR.exists():
        raise FileNotFoundError(
            f"Ordner nicht gefunden: {DEBUG_DIR}"
        )

    files = sorted(
        DEBUG_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:MAX_FILES]

    if not files:
        raise FileNotFoundError(
            "Keine Liveticker-JSONs gefunden."
        )

    print("=" * 80)
    print("NEUESTE LIVETICKER-JSONS")
    print("=" * 80)

    for file_path in files:
        print()
        print(file_path.name)

        try:
            data = json.loads(
                file_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as error:
            print(f"  Fehler: {error}")
            continue

        events = get_events(data)

        goals = [
            event
            for event in events
            if is_goal_event(event)
        ]

        print(
            f"  Events gesamt: {len(events)}"
        )
        print(
            f"  Tor-Events: {len(goals)}"
        )

        for event in sorted(
            goals,
            key=lambda item: (
                item.get("minute") or 0,
                item.get("minute_additional") or 0,
            ),
        ):
            print(
                "   "
                f"{event.get('minute')}"
                f"+{event.get('minute_additional') or 0} | "
                f"type={event.get('type_id')} | "
                f"score={event.get('score')} | "
                f"team={event.get('team_id')} | "
                f"{event.get('description')}"
            )

    print()
    print("=" * 80)
    print("ENDE")
    print("=" * 80)


if __name__ == "__main__":
    main()
