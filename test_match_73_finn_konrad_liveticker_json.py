from __future__ import annotations

import json
import re
from pathlib import Path


MATCH_EXTERNAL_ID = "02TNB07ETS000000VS5489BUVSSD35NB"

LIVETICKER_JSON_PATH = Path(
    "debug/liveticker/"
    f"{MATCH_EXTERNAL_ID}.json"
)

MATCH_HTML_PATH = Path(
    "debug/html/matches/"
    f"{MATCH_EXTERNAL_ID}.html"
)

FINN_EXTERNAL_ID = "012SVM882G000000VV0AG811VT70LNAS"

TARGET_MINUTES = {
    71,
    86,
}


def normalize_text(
    value: object,
) -> str:
    return " ".join(
        str(value or "")
        .replace("\xa0", " ")
        .split()
    )


def recursive_find(
    value: object,
    path: str = "$",
) -> list[tuple[str, object]]:
    matches: list[
        tuple[str, object]
    ] = []

    if isinstance(
        value,
        dict,
    ):
        for key, child in value.items():
            child_path = (
                f"{path}.{key}"
            )

            text = normalize_text(
                child
            )

            if (
                FINN_EXTERNAL_ID
                in text
            ):
                matches.append(
                    (
                        child_path,
                        child,
                    )
                )

            matches.extend(
                recursive_find(
                    child,
                    child_path,
                )
            )

    elif isinstance(
        value,
        list,
    ):
        for index, child in enumerate(
            value
        ):
            child_path = (
                f"{path}[{index}]"
            )

            text = normalize_text(
                child
            )

            if (
                FINN_EXTERNAL_ID
                in text
            ):
                matches.append(
                    (
                        child_path,
                        child,
                    )
                )

            matches.extend(
                recursive_find(
                    child,
                    child_path,
                )
            )

    return matches


def extract_possible_minute(
    event: object,
) -> int | None:
    if not isinstance(
        event,
        dict,
    ):
        return None

    candidate_keys = (
        "minute",
        "matchMinute",
        "match_minute",
        "time",
        "eventMinute",
        "event_minute",
    )

    for key in candidate_keys:
        if key not in event:
            continue

        raw = event.get(
            key
        )

        if raw is None:
            continue

        if isinstance(
            raw,
            int,
        ):
            return raw

        match = re.search(
            r"\d{1,3}",
            str(raw),
        )

        if match:
            return int(
                match.group(0)
            )

    text = normalize_text(
        event
    )

    minute_match = re.search(
        r"(?<!\d)(71|86)(?!\d)",
        text,
    )

    if minute_match:
        return int(
            minute_match.group(1)
        )

    return None


def print_event(
    index: int,
    event: object,
) -> None:
    print()
    print("-" * 110)
    print(
        f"EVENT INDEX {index}"
    )
    print("-" * 110)

    if isinstance(
        event,
        dict,
    ):
        minute = extract_possible_minute(
            event
        )

        print(
            f"Erkannte Minute: {minute}"
        )

    print(
        json.dumps(
            event,
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 73 / FINN KONRAD - "
        "LIVETICKER-JSON VS MATCH-HTML"
    )
    print("=" * 110)

    print(
        f"Match-ID: {MATCH_EXTERNAL_ID}"
    )
    print(
        f"Finn-ID:  {FINN_EXTERNAL_ID}"
    )

    print()
    print("DATEIEN")
    print("-" * 110)
    print(
        f"Liveticker JSON: "
        f"{LIVETICKER_JSON_PATH}"
    )
    print(
        f"Match HTML:      "
        f"{MATCH_HTML_PATH}"
    )

    if not LIVETICKER_JSON_PATH.exists():
        print()
        print(
            "ERGEBNIS: Kein gespeichertes "
            "Liveticker-JSON für Spiel 73 "
            "gefunden."
        )
        print(
            "Dann wurde der 71'-Wechsel "
            "wahrscheinlich aus einer anderen "
            "Importquelle erzeugt."
        )
        return

    payload = json.loads(
        LIVETICKER_JSON_PATH.read_text(
            encoding="utf-8",
        )
    )

    events = (
        payload.get(
            "events",
            [],
        )
        if isinstance(
            payload,
            dict,
        )
        else []
    )

    print()
    print("LIVETICKER")
    print("-" * 110)
    print(
        f"Events im JSON: {len(events)}"
    )

    finn_events: list[
        tuple[int, object]
    ] = []

    target_minute_events: list[
        tuple[int, object]
    ] = []

    for index, event in enumerate(
        events
    ):
        event_text = json.dumps(
            event,
            ensure_ascii=False,
        )

        minute = extract_possible_minute(
            event
        )

        if (
            FINN_EXTERNAL_ID
            in event_text
        ):
            finn_events.append(
                (
                    index,
                    event,
                )
            )

        if minute in TARGET_MINUTES:
            target_minute_events.append(
                (
                    index,
                    event,
                )
            )

    print(
        f"Events mit Finn-ID: "
        f"{len(finn_events)}"
    )
    print(
        f"Events bei 71'/86': "
        f"{len(target_minute_events)}"
    )

    print()
    print("=" * 110)
    print(
        "LIVETICKER-EVENTS MIT FINN-ID"
    )
    print("=" * 110)

    if not finn_events:
        print("(keine)")
    else:
        for index, event in finn_events:
            print_event(
                index,
                event,
            )

    print()
    print("=" * 110)
    print(
        "ALLE LIVETICKER-EVENTS 71'/86'"
    )
    print("=" * 110)

    if not target_minute_events:
        print("(keine)")
    else:
        for index, event in target_minute_events:
            print_event(
                index,
                event,
            )

    deep_matches = recursive_find(
        payload
    )

    print()
    print("=" * 110)
    print(
        "ALLE JSON-PFADE MIT FINN-ID"
    )
    print("=" * 110)

    if not deep_matches:
        print("(keine)")
    else:
        seen: set[str] = set()

        for path, value in deep_matches:
            if path in seen:
                continue

            seen.add(
                path
            )

            print(
                f"{path}: "
                f"{normalize_text(value)[:500]}"
            )

    html_occurrences = 0

    if MATCH_HTML_PATH.exists():
        html = MATCH_HTML_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        )

        html_occurrences = html.count(
            FINN_EXTERNAL_ID
        )

    print()
    print("=" * 110)
    print("VERGLEICH")
    print("=" * 110)
    print(
        f"Finn-ID im Match-HTML: "
        f"{html_occurrences} Vorkommen"
    )
    print(
        f"Finn-ID im Liveticker-JSON: "
        f"{len(finn_events)} Event(s)"
    )

    finn_minutes = sorted(
        minute
        for _, event in finn_events
        if (
            minute := extract_possible_minute(
                event
            )
        ) is not None
    )

    print(
        f"Finn-Minuten im Liveticker: "
        f"{finn_minutes}"
    )

    print()

    if finn_minutes == [71]:
        print(
            "BEFUND: Liveticker liefert Finn "
            "nur in 71'. Das 86'-Event stammt "
            "aus dem Match-HTML."
        )
        print(
            "Dann wurden zwei unterschiedliche "
            "Quellen zu einer widersprüchlichen "
            "Wechselhistorie kombiniert."
        )

    elif finn_minutes == [86]:
        print(
            "BEFUND: Liveticker liefert Finn "
            "nur in 86'. Der 71'-Datensatz muss "
            "aus einer anderen Quelle stammen."
        )

    elif (
        71 in finn_minutes
        and 86 in finn_minutes
    ):
        print(
            "BEFUND: Bereits das Liveticker-JSON "
            "enthält Finn bei 71' und 86'."
        )
        print(
            "Dann ist die Doppel-Einwechslung "
            "quellseitig vorhanden."
        )

    elif not finn_minutes:
        print(
            "BEFUND: Finn taucht im gespeicherten "
            "Liveticker-JSON nicht als direkt "
            "erkennbares Event auf."
        )
        print(
            "Dann liegt die 71'-Zuordnung sehr "
            "wahrscheinlich in Parser-/"
            "ID-Auflösungslogik."
        )

    else:
        print(
            "BEFUND: Ungewöhnliche "
            "Liveticker-Konstellation."
        )
        print(
            "Die oben ausgegebenen JSON-Events "
            "zeigen die genaue Ursache."
        )

    print("=" * 110)


if __name__ == "__main__":
    main()
