from __future__ import annotations

import json
from pathlib import Path

from src.importer.fussballde.liveticker_parser import (
    LivetickerParser,
)


MATCH_ID = "031BG6B7PG000000VS5489BUVUR5FS5A"

GOAL_TYPES = {
    "goal",
    "own_goal",
    "penalty_goal",
}


def find_candidate_files(
    root: Path,
) -> list[Path]:
    candidates: list[Path] = []

    ignored_parts = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
    }

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in ignored_parts
            for part in path.parts
        ):
            continue

        if path.suffix.lower() not in {
            ".html",
            ".htm",
            ".json",
            ".txt",
        }:
            continue

        if MATCH_ID.casefold() in path.name.casefold():
            candidates.append(path)

    return sorted(candidates)


def load_content(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    if path.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    return text


def print_event(
    index: int,
    event,
) -> None:
    marker = (
        " <<< TOR"
        if event.event_type in GOAL_TYPES
        else ""
    )

    score = ""

    if (
        event.score_home is not None
        and event.score_away is not None
    ):
        score = (
            f"{event.score_home}:"
            f"{event.score_away}"
        )

    minute = (
        "?"
        if event.minute is None
        else str(event.minute)
    )

    if event.additional_time:
        minute += (
            f"+{event.additional_time}"
        )

    print(
        f"{index:>2}. "
        f"{minute:>6} | "
        f"{event.event_type:<18} | "
        f"{score:<5} | "
        f"{event.player or '-'}"
        f"{marker}"
    )

    print(
        "    Team: "
        f"{event.team or '-'}"
    )

    print(
        "    Beschreibung: "
        f"{event.description or '-'}"
    )

    if event.source_event_id:
        print(
            "    Event-ID: "
            f"{event.source_event_id}"
        )

    print()


def diagnose_file(
    parser: LivetickerParser,
    path: Path,
) -> None:
    print("=" * 100)
    print(f"DATEI: {path}")
    print("=" * 100)

    try:
        content = load_content(path)

        data = parser.parse_auto(
            content=content,
            match_id=MATCH_ID,
        )

    except Exception as exc:
        print(
            "Parser-Fehler: "
            f"{type(exc).__name__}: {exc}"
        )
        print()
        return

    print(
        "Quelle: "
        f"{data.source_type}"
    )
    print(
        "Ticker verfügbar: "
        f"{data.ticker_available}"
    )
    print(
        "Teams: "
        f"{data.home_team or '?'} - "
        f"{data.away_team or '?'}"
    )
    print(
        "Ergebnis laut Liveticker: "
        f"{data.home_score}:"
        f"{data.away_score}"
    )
    print(
        "Events insgesamt: "
        f"{len(data.events)}"
    )

    goal_events = [
        event
        for event in data.events
        if event.event_type in GOAL_TYPES
    ]

    print(
        "Als Tor klassifiziert: "
        f"{len(goal_events)}"
    )

    print()
    print("ALLE EVENTS")
    print("-" * 100)

    for index, event in enumerate(
        data.events,
        start=1,
    ):
        print_event(
            index=index,
            event=event,
        )

    print()
    print("NUR TOR-EVENTS")
    print("-" * 100)

    if not goal_events:
        print(
            "Keine Tor-Events erkannt."
        )

    for index, event in enumerate(
        goal_events,
        start=1,
    ):
        print_event(
            index=index,
            event=event,
        )

    if data.warnings:
        print("WARNUNGEN")
        print("-" * 100)

        for warning in data.warnings:
            print(
                f"- {warning}"
            )

    print()


def main() -> None:
    root = Path.cwd()

    print("=" * 100)
    print(
        "LIVETICKER-DIAGNOSE "
        "COTTBUS - HANNOVER"
    )
    print("=" * 100)
    print(
        f"Spiel-ID: {MATCH_ID}"
    )
    print(
        f"Projekt:  {root}"
    )
    print()

    candidates = find_candidate_files(
        root
    )

    if not candidates:
        print(
            "Keine HTML/JSON/TXT-Datei mit "
            "dieser Spiel-ID im Dateinamen "
            "gefunden."
        )
        print()
        print(
            "Suche im Explorer nach:"
        )
        print(MATCH_ID)
        return

    print(
        "Gefundene Kandidaten: "
        f"{len(candidates)}"
    )

    for path in candidates:
        print(
            f"- {path}"
        )

    print()

    parser = LivetickerParser()

    for path in candidates:
        diagnose_file(
            parser=parser,
            path=path,
        )


if __name__ == "__main__":
    main()
