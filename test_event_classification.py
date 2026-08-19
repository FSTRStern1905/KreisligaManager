from __future__ import annotations

import json
from pathlib import Path

from src.importer.fussballde.liveticker_parser import LivetickerParser


DEBUG_DIR = Path("debug/liveticker/json")

MATCH_IDS = (
    "02TNB07C4O000000VS5489BUVSSD35NB",
    "02TNB07C5S000000VS5489BUVSSD35NB",
    "02TNB07C6S000000VS5489BUVSSD35NB",
)

GOAL_TYPES = {
    "goal",
    "penalty_goal",
    "own_goal",
}


def main() -> None:
    parser = LivetickerParser()

    print("=" * 90)
    print("EVENT-KLASSIFIKATIONS-DIAGNOSE")
    print("=" * 90)

    for match_id in MATCH_IDS:
        file_path = DEBUG_DIR / f"{match_id}.json"

        print()
        print("=" * 90)
        print(match_id)
        print("=" * 90)

        if not file_path.exists():
            print(f"JSON fehlt: {file_path}")
            continue

        payload = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

        data = parser.parse_json(
            payload=payload,
            match_id=match_id,
        )

        print(
            f"Parser-Events gesamt: {len(data.events)}"
        )

        parsed_goal_count = 0

        for event in sorted(
            data.events,
            key=lambda item: (
                item.minute
                if item.minute is not None
                else -1,
                item.additional_time,
                item.source_event_id,
            ),
        ):
            raw = (
                event.raw_data
                if isinstance(event.raw_data, dict)
                else {}
            )

            raw_type_id = raw.get("type_id")

            if event.event_type in GOAL_TYPES:
                parsed_goal_count += 1
                marker = "<<< TOR-IMPORT"
            else:
                marker = ""

            print(
                f"{event.minute!s:>3}"
                f"+{event.additional_time:<2} | "
                f"type_id={str(raw_type_id):>4} | "
                f"parsed={event.event_type:<18} | "
                f"score={str(raw.get('score')):<5} | "
                f"{event.description} "
                f"{marker}"
            )

        print()
        print(
            f"Als Tore klassifiziert: "
            f"{parsed_goal_count}"
        )

    print()
    print("=" * 90)
    print("DIAGNOSE ENDE")
    print("=" * 90)


if __name__ == "__main__":
    main()
