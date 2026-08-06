from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from src.importer.fussballde.liveticker_json_parser import (
    LivetickerJsonParser,
)


SOURCES = (
    Path(
        "02TKDR2LFG000000VS5489BUVUD1610F.zip"
    ),
    Path(
        "02TNB07DS8000000VS5489BUVSSD35NB.zip"
    ),
)


def find_liveticker_payload(
    zip_path: Path,
) -> tuple[str, dict[str, Any]]:
    with zipfile.ZipFile(
        zip_path
    ) as archive:
        candidates: list[
            tuple[str, dict[str, Any]]
        ] = []

        for name in archive.namelist():
            if not name.casefold().endswith(
                ".json"
            ):
                continue

            try:
                payload = json.loads(
                    archive.read(
                        name
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )
                )
            except (
                json.JSONDecodeError,
                UnicodeDecodeError,
            ):
                continue

            if not isinstance(
                payload,
                dict,
            ):
                continue

            events = payload.get(
                "events"
            )

            if not isinstance(
                events,
                list,
            ):
                continue

            score = 0

            normalized_name = (
                name.casefold()
            )

            if "ajax.liveticker" in normalized_name:
                score += 100

            if "liveticker_enabled" in payload:
                score += 30

            if "home_team" in payload:
                score += 20

            if "guest_team" in payload:
                score += 20

            if events:
                score += 10

            candidates.append(
                (
                    f"{score:04d}:{name}",
                    payload,
                )
            )

        if not candidates:
            raise ValueError(
                "Keine Liveticker-JSON-Datei "
                f"in {zip_path.name} gefunden."
            )

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        scored_name, payload = candidates[0]

        _, name = scored_name.split(
            ":",
            1,
        )

        return name, payload


def print_event(
    index: int,
    event,
) -> None:
    print(
        f"[{index:02d}] "
        f"{event.display_minute:>5} "
        f"{event.event_type}"
    )

    if event.team:
        print(
            f"     Team:       "
            f"{event.team}"
        )

    if event.player:
        print(
            f"     Spieler:    "
            f"{event.player}"
        )

    if event.player_id:
        print(
            f"     Spieler-ID: "
            f"{event.player_id}"
        )

    if event.player_out:
        print(
            f"     Spieler 2:  "
            f"{event.player_out}"
        )

    if event.player_out_id:
        print(
            f"     Spieler2-ID:"
            f" {event.player_out_id}"
        )

    if event.has_score:
        print(
            f"     Spielstand: "
            f"{event.score_home}:"
            f"{event.score_away}"
        )

    if event.description:
        print(
            f"     Text:       "
            f"{event.description}"
        )


def validate_result(
    source_name: str,
    data,
) -> None:
    assert data.match_id, (
        f"{source_name}: Keine Match-ID."
    )

    assert data.home_team, (
        f"{source_name}: Heimteam fehlt."
    )

    assert data.away_team, (
        f"{source_name}: Auswärtsteam fehlt."
    )

    assert data.event_count > 0, (
        f"{source_name}: Keine Events."
    )

    goals = data.get_events_by_type(
        "goal"
    )

    for event in goals:
        assert event.team, (
            f"{source_name}: Tor ohne Team."
        )
        assert event.player, (
            f"{source_name}: Tor ohne Spieler."
        )
        assert event.player_id, (
            f"{source_name}: Tor ohne Spieler-ID."
        )

    yellow_cards = data.get_events_by_type(
        "yellow_card"
    )

    for event in yellow_cards:
        assert event.team, (
            f"{source_name}: Gelbe Karte "
            "ohne Team."
        )
        assert event.player, (
            f"{source_name}: Gelbe Karte "
            "ohne Spieler."
        )

    substitutions = data.get_events_by_type(
        "substitution"
    )

    for event in substitutions:
        assert event.team, (
            f"{source_name}: Wechsel ohne Team."
        )
        assert event.player, (
            f"{source_name}: Wechsel ohne "
            "ersten Spieler."
        )
        assert event.player_out, (
            f"{source_name}: Wechsel ohne "
            "zweiten Spieler."
        )


def print_result(
    zip_path: Path,
    json_name: str,
    data,
) -> None:
    print()
    print("=" * 90)
    print(
        f"TEST: {zip_path.name}"
    )
    print("=" * 90)
    print(
        f"JSON-Datei:            "
        f"{json_name}"
    )
    print(
        f"Spiel-ID:              "
        f"{data.match_id}"
    )
    print(
        f"Partie:                "
        f"{data.home_team} - "
        f"{data.away_team}"
    )
    print(
        f"Spielstand:            "
        f"{data.home_score}:"
        f"{data.away_score}"
    )
    print(
        f"Liveticker aktiviert:  "
        f"{'JA' if data.ticker_available else 'NEIN'}"
    )
    print(
        f"Events:                "
        f"{data.event_count}"
    )
    print(
        f"Mit Spielerzuordnung:  "
        f"{data.assigned_event_count}"
    )
    print(
        f"Ohne Spielerzuordnung: "
        f"{data.unassigned_event_count}"
    )
    print(
        f"Zuordnungsquote:       "
        f"{data.player_assignment_rate:.1f} %"
    )

    event_counts = {
        event_type: len(
            data.get_events_by_type(
                event_type
            )
        )
        for event_type in (
            "goal",
            "yellow_card",
            "substitution",
            "corner",
            "offside",
            "kickoff",
            "fulltime",
            "unknown",
        )
    }

    print()
    print("EVENTTYPEN")
    print("-" * 90)

    for event_type, count in (
        event_counts.items()
    ):
        print(
            f"{event_type:18} "
            f"{count}"
        )

    print()
    print("EREIGNISSE")
    print("-" * 90)

    for index, event in enumerate(
        data.events,
        start=1,
    ):
        print_event(
            index,
            event,
        )

    if data.warnings:
        print()
        print("WARNUNGEN")
        print("-" * 90)

        for warning in data.warnings:
            print(
                f"⚠ {warning}"
            )


def main() -> None:
    print("=" * 90)
    print("LIVETICKER JSON PARSER TEST")
    print("=" * 90)

    missing_sources = [
        source
        for source in SOURCES
        if not source.exists()
    ]

    if missing_sources:
        print()
        print("FEHLENDE ZIP-DATEIEN")
        print("-" * 90)

        for source in missing_sources:
            print(
                source
            )

        print()
        print(
            "Lege beide ZIP-Dateien in:"
        )
        print(
            r"E:\Kreisligamanager"
        )
        return

    parser = LivetickerJsonParser()

    tested_files = 0
    total_events = 0

    for source in SOURCES:
        json_name, payload = (
            find_liveticker_payload(
                source
            )
        )

        data = parser.parse(
            payload=payload,
            source_url=(
                f"zip://{source.name}/"
                f"{json_name}"
            ),
        )

        print_result(
            zip_path=source,
            json_name=json_name,
            data=data,
        )

        validate_result(
            source_name=source.name,
            data=data,
        )

        tested_files += 1
        total_events += data.event_count

    print()
    print("=" * 90)
    print(
        "ALLE LIVETICKER-JSON-TESTS "
        "ERFOLGREICH"
    )
    print("=" * 90)
    print(
        f"Getestete Spiele: "
        f"{tested_files}"
    )
    print(
        f"Geprüfte Events:  "
        f"{total_events}"
    )


if __name__ == "__main__":
    main()