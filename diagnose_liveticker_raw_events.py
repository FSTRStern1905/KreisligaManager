from __future__ import annotations

import json
from pathlib import Path


MATCH_ID = "031BG6B7PG000000VS5489BUVUR5FS5A"

JSON_PATH = Path(
    "debug/liveticker/json"
) / f"{MATCH_ID}.json"


def load_payload() -> dict | list:
    if not JSON_PATH.exists():
        raise FileNotFoundError(
            f"JSON-Datei fehlt: {JSON_PATH}"
        )

    text = JSON_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    return json.loads(text)


def iter_dicts(
    value,
):
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from iter_dicts(child)

    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def get_text(
    item: dict,
) -> str:
    values = []

    for key in (
        "description",
        "text",
        "comment",
        "message",
        "content",
        "title",
        "headline",
        "label",
        "type",
        "eventType",
        "event_type",
        "kind",
        "category",
    ):
        value = item.get(key)

        if isinstance(value, str):
            values.append(value)

    return " ".join(values).casefold()


def find_event(
    payload,
    event_kind: str,
) -> dict | None:
    for item in iter_dicts(payload):
        text = get_text(item)

        if event_kind == "goal":
            if (
                "tor" in text
                or "goal" in text
            ):
                return item

        elif event_kind == "yellow_card":
            if (
                "gelbe karte" in text
                or "yellow card" in text
                or "yellow_card" in text
            ):
                return item

        elif event_kind == "substitution":
            if (
                "wechsel" in text
                or "substitution" in text
                or "auswechslung" in text
                or "einwechslung" in text
            ):
                return item

    return None


def print_event(
    title: str,
    event: dict | None,
) -> None:
    print("=" * 100)
    print(title)
    print("=" * 100)

    if event is None:
        print("Kein passender Rohdatensatz gefunden.")
        print()
        return

    print(
        json.dumps(
            event,
            ensure_ascii=False,
            indent=2,
        )
    )
    print()


def main() -> None:
    print("=" * 100)
    print("LIVETICKER-JSON ROHDATEN-DIAGNOSE")
    print("=" * 100)
    print(f"Spiel-ID: {MATCH_ID}")
    print(f"Datei:    {JSON_PATH}")
    print()

    payload = load_payload()

    print_event(
        "TOR",
        find_event(
            payload,
            "goal",
        ),
    )

    print_event(
        "GELBE KARTE",
        find_event(
            payload,
            "yellow_card",
        ),
    )

    print_event(
        "WECHSEL",
        find_event(
            payload,
            "substitution",
        ),
    )


if __name__ == "__main__":
    main()
