from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.importer.fussballde.liveticker_json_parser import (
    LivetickerJsonParser,
)


MATCH_ID = "02TKDR1R4S000000VS5489BUVUD1610F"
JSON_PATH = Path("debug/liveticker/json") / f"{MATCH_ID}.json"


def normalize_score(value) -> str:
    if isinstance(value, dict):
        home = value.get("home", value.get("homeScore", "?"))
        away = value.get("away", value.get("awayScore", "?"))
        return f"{home}:{away}"

    return str(value or "-")


def main() -> None:
    print("=" * 100)
    print("LIVETICKER DIAGNOSE – SPIEL 4")
    print("=" * 100)
    print(f"Spiel-ID: {MATCH_ID}")
    print(f"JSON:     {JSON_PATH}")
    print()

    if not JSON_PATH.exists():
        print("FEHLER:")
        print("Die Debug-JSON-Datei wurde nicht gefunden.")
        print()
        print("Erwarteter Pfad:")
        print(JSON_PATH.resolve())
        return

    payload = json.loads(
        JSON_PATH.read_text(
            encoding="utf-8",
        )
    )

    raw_events = payload.get("events", [])

    if not isinstance(raw_events, list):
        raise ValueError("payload['events'] ist keine Liste.")

    parser = LivetickerJsonParser()

    parsed = parser.parse(
        payload=payload,
        source_url="",
    )

    print("SPIEL")
    print("-" * 100)
    print(f"{parsed.home_team} - {parsed.away_team}")
    print(
        "Endstand laut Liveticker: "
        f"{parsed.home_score}:{parsed.away_score}"
    )
    print(f"Roh-Events:              {len(raw_events)}")
    print(f"Geparste Events:         {len(parsed.events)}")
    print()

    raw_type_counts = Counter()

    for event in raw_events:
        if not isinstance(event, dict):
            continue

        raw_type_counts[event.get("type_id")] += 1

    parsed_type_counts = Counter(
        event.event_type
        for event in parsed.events
    )

    print("RAW TYPE-IDS")
    print("-" * 100)

    for type_id, count in sorted(
        raw_type_counts.items(),
        key=lambda item: str(item[0]),
    ):
        mapped = parser.EVENT_TYPE_BY_ID.get(
            parser._to_integer(type_id),
            "unknown",
        )

        print(
            f"type_id={str(type_id):>4} | "
            f"{count:>3}x | "
            f"Parser: {mapped}"
        )

    print()
    print("PARSED EVENTTYPEN")
    print("-" * 100)

    for event_type, count in sorted(
        parsed_type_counts.items()
    ):
        print(f"{event_type:<20} {count}")

    print()
    print("ALLE RAW-EVENTS")
    print("-" * 100)

    for index, event in enumerate(
        raw_events,
        start=1,
    ):
        if not isinstance(event, dict):
            print(f"[{index:02}] Ungültiges Eventformat")
            continue

        type_id = event.get("type_id")

        parsed_type = parser.EVENT_TYPE_BY_ID.get(
            parser._to_integer(type_id),
            "unknown",
        )

        minute = event.get("minute", "-")
        additional = event.get("minute_additional", 0)

        minute_text = str(minute)

        if additional:
            minute_text += f"+{additional}"

        score = normalize_score(
            event.get("score")
        )

        description = str(
            event.get("description", "")
            or ""
        ).strip()

        comment = str(
            event.get("comment", "")
            or ""
        ).strip()

        member_id = str(
            event.get("member_id", "")
            or ""
        ).strip()

        member2_id = str(
            event.get("member2_id", "")
            or ""
        ).strip()

        print(
            f"[{index:02}] "
            f"{minute_text:>5} | "
            f"type_id={str(type_id):>3} | "
            f"{parsed_type:<14} | "
            f"Score {score:<7}"
        )

        if description:
            print(f"     Beschreibung: {description}")

        if comment:
            print(f"     Kommentar:     {comment}")

        if member_id:
            print(f"     member_id:     {member_id}")

        if member2_id:
            print(f"     member2_id:    {member2_id}")

    print()
    print("TOR-CHECK")
    print("-" * 100)

    expected_goals = 0

    if (
        parsed.home_score is not None
        and parsed.away_score is not None
    ):
        expected_goals = (
            parsed.home_score
            + parsed.away_score
        )

    parsed_goals = sum(
        1
        for event in parsed.events
        if event.event_type == "goal"
    )

    unknown_with_score = [
        event
        for event in parsed.events
        if (
            event.event_type == "unknown"
            and event.has_score
        )
    ]

    print(f"Tore laut Endstand:      {expected_goals}")
    print(f"Als 'goal' erkannt:      {parsed_goals}")
    print(f"Unknown mit Spielstand:  {len(unknown_with_score)}")

    if unknown_with_score:
        print()
        print("VERDÄCHTIGE UNKNOWN-EVENTS")
        print("-" * 100)

        for event in unknown_with_score:
            print(
                f"{event.minute}. Minute | "
                f"{event.score_home}:"
                f"{event.score_away} | "
                f"type_id="
                f"{event.raw_data.get('type_id')} | "
                f"{event.description}"
            )

    print()
    print("=" * 100)

    if parsed_goals == expected_goals:
        print(
            "ERGEBNIS: Parser erkennt die "
            "korrekte Anzahl Tore."
        )
        print(
            "Dann liegt der Verlust NACH dem "
            "LivetickerJsonParser."
        )
    else:
        print(
            "ERGEBNIS: Parser erkennt NICHT "
            "alle Tore."
        )
        print(
            "Damit ist der Fehler auf "
            "Liveticker-Type-ID/Parsing eingegrenzt."
        )

    print("=" * 100)


if __name__ == "__main__":
    main()
