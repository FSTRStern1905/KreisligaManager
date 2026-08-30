from __future__ import annotations

import re
from pathlib import Path
from bs4 import BeautifulSoup


MATCH_EXTERNAL_ID = "02TNUVBCCK000000VS5489BUVSSD35NB"

CANDIDATES = [
    Path(
        f"debug/html/matches/{MATCH_EXTERNAL_ID}.html"
    ),
    Path(
        f"debug/liveticker/{MATCH_EXTERNAL_ID}.json"
    ),
    Path(
        f"debug/liveticker/{MATCH_EXTERNAL_ID}.html"
    ),
]


def separator(title: str) -> None:
    print()
    print("=" * 110)
    print(title)
    print("=" * 110)


def inspect_html(path: Path) -> None:
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    soup = BeautifulSoup(
        text,
        "html.parser",
    )

    separator(f"HTML: {path}")
    print(f"Größe: {len(text)} Zeichen")

    event_rows = soup.select(
        ".row-event, "
        "[class*='event-']"
    )

    seen = set()
    interesting = []

    for row in event_rows:
        raw = " ".join(
            row.stripped_strings
        )
        if not raw:
            continue

        key = str(row)
        if key in seen:
            continue
        seen.add(key)

        normalized = raw.lower()

        if (
            "tor" in normalized
            or "elfmeter" in normalized
            or re.search(
                r"\b[0-9]+\s*:\s*[0-9]+\b",
                raw,
            )
        ):
            interesting.append(
                (raw, row)
            )

    print(
        f"Interessante Event-Zeilen: "
        f"{len(interesting)}"
    )

    for index, (raw, row) in enumerate(
        interesting,
        start=1,
    ):
        print()
        print("-" * 110)
        print(f"[{index}] TEXT")
        print(raw)

        minute = None
        minute_match = re.search(
            r"(\d+)\s*[’']",
            raw,
        )
        if minute_match:
            minute = minute_match.group(1)

        score_matches = re.findall(
            r"\b(\d+)\s*:\s*(\d+)\b",
            raw,
        )

        print(
            f"Minute: {minute or '-'}"
        )
        print(
            f"Spielstände: "
            f"{score_matches or '-'}"
        )

        links = row.select(
            "a[href*='spielerprofil'], "
            "a[href*='player-id']"
        )

        if links:
            print("Spielerlinks:")
            for link in links:
                print(
                    "  "
                    + link.get(
                        "href",
                        "",
                    )
                )

    separator("TEXTSUCHE NACH 6:0")
    patterns = [
        "6:0",
        "6 : 0",
        "5:0",
        "5 : 0",
    ]

    for pattern in patterns:
        count = text.count(pattern)
        print(
            f"{pattern!r}: {count}"
        )

        if count:
            positions = [
                match.start()
                for match in re.finditer(
                    re.escape(pattern),
                    text,
                )
            ]

            for position in positions[:5]:
                start = max(
                    0,
                    position - 300,
                )
                end = min(
                    len(text),
                    position + 500,
                )
                snippet = re.sub(
                    r"\s+",
                    " ",
                    text[start:end],
                )
                print(
                    f"  ...{snippet}..."
                )


def inspect_text_file(path: Path) -> None:
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    separator(f"DATEI: {path}")
    print(f"Größe: {len(text)} Zeichen")

    patterns = [
        "6:0",
        "6 : 0",
        "5:0",
        "5 : 0",
        "goal",
        "tor",
    ]

    for pattern in patterns:
        count = text.lower().count(
            pattern.lower()
        )
        print(
            f"{pattern!r}: {count}"
        )

    separator(
        f"AUSSCHNITTE AUS {path.name}"
    )

    score_regex = re.compile(
        r".{0,250}"
        r"(?:6\s*:\s*0|5\s*:\s*0)"
        r".{0,500}",
        re.IGNORECASE
        | re.DOTALL,
    )

    matches = score_regex.findall(
        text
    )

    if not matches:
        print(
            "Keine 5:0/6:0-Ausschnitte gefunden."
        )
        return

    for index, snippet in enumerate(
        matches[:20],
        start=1,
    ):
        print()
        print("-" * 110)
        print(f"[{index}]")
        print(
            re.sub(
                r"\s+",
                " ",
                snippet,
            )
        )


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 658 / ROHQUELLEN-DIAGNOSE "
        "FÜR DAS FEHLENDE 6:0"
    )
    print("=" * 110)
    print(
        f"Match external_id: "
        f"{MATCH_EXTERNAL_ID}"
    )
    print(
        "Keine Datenbankänderung."
    )

    existing = [
        path
        for path in CANDIDATES
        if path.exists()
    ]

    separator("GEFUNDENE DATEIEN")

    if not existing:
        print(
            "Keine gespeicherte Rohquelle gefunden."
        )
        print(
            "Geprüfte Pfade:"
        )
        for path in CANDIDATES:
            print(
                f"  {path}"
            )
        return

    for path in existing:
        print(path)

    for path in existing:
        if path.suffix.lower() == ".html":
            inspect_html(path)
        else:
            inspect_text_file(path)

    separator("NÄCHSTER BEFUND")
    print(
        "Wenn die Rohquelle ein 6:0 enthält, "
        "lokalisieren wir anschließend exakt, "
        "warum der Event-Parser dieses Tor "
        "nicht übernommen hat."
    )
    print(
        "Wenn bereits die Rohquelle nur bis 5:0 "
        "geht, ist die Abweichung quellseitig."
    )


if __name__ == "__main__":
    main()
