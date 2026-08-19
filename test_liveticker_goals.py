from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEBUG_DIR = Path("debug/liveticker/json")


def walk(value: Any, path: str = "root"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def looks_like_goal_event(item: dict[str, Any]) -> bool:
    type_id = item.get("type_id")
    event_type = str(
        item.get("type")
        or item.get("event_type")
        or item.get("eventType")
        or ""
    ).casefold()

    text = " ".join(
        str(item.get(key) or "")
        for key in (
            "text",
            "description",
            "comment",
            "title",
            "event_text",
        )
    ).casefold()

    return (
        type_id == 1
        or "goal" in event_type
        or "tor" in text
        or "elfmeter" in text
        or "eigentor" in text
    )


def compact(item: dict[str, Any]) -> dict[str, Any]:
    wanted = (
        "id",
        "type_id",
        "type",
        "event_type",
        "eventType",
        "minute",
        "minute_additional",
        "additional_minute",
        "score",
        "result",
        "home_score",
        "away_score",
        "team",
        "team_id",
        "player",
        "player_name",
        "text",
        "description",
        "comment",
        "title",
    )

    result = {}

    for key in wanted:
        if key in item:
            result[key] = item[key]

    return result


def main() -> None:
    if not DEBUG_DIR.exists():
        raise FileNotFoundError(
            f"Ordner nicht gefunden: {DEBUG_DIR}"
        )

    files = sorted(DEBUG_DIR.glob("*.json"))

    if not files:
        raise FileNotFoundError(
            f"Keine JSON-Dateien in {DEBUG_DIR}"
        )

    print("=" * 80)
    print("LIVETICKER-TOR-DIAGNOSE")
    print("=" * 80)
    print(f"JSON-Dateien gefunden: {len(files)}")

    for file_path in files:
        print()
        print("=" * 80)
        print(file_path.name)
        print("=" * 80)

        try:
            data = json.loads(
                file_path.read_text(encoding="utf-8")
            )
        except Exception as error:
            print(f"JSON konnte nicht gelesen werden: {error}")
            continue

        matches = []

        for path, item in walk(data):
            if looks_like_goal_event(item):
                matches.append((path, item))

        print(
            f"Mögliche Tor-Datensätze: {len(matches)}"
        )

        seen = set()

        for index, (path, item) in enumerate(
            matches,
            start=1,
        ):
            values = compact(item)

            signature = json.dumps(
                values,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )

            duplicate = signature in seen
            seen.add(signature)

            marker = "DUPLIKAT" if duplicate else "EVENT"

            print()
            print(
                f"[{index}] {marker} | {path}"
            )

            if values:
                print(
                    json.dumps(
                        values,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )
                )
            else:
                print(
                    json.dumps(
                        item,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )[:2500]
                )

    print()
    print("=" * 80)
    print("DIAGNOSE ABGESCHLOSSEN")
    print("=" * 80)


if __name__ == "__main__":
    main()
