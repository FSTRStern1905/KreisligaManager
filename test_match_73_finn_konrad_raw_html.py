from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup


MATCH_EXTERNAL_ID = "02TNB07ETS000000VS5489BUVSSD35NB"

HTML_PATH = Path(
    "debug/html/matches/"
    f"{MATCH_EXTERNAL_ID}.html"
)

FINN_EXTERNAL_IDS = {
    "012SVM882G000000VV0AG811VT70LNAS",
}

TARGET_MINUTES = {
    71,
    86,
}


PLAYER_ID_PATTERNS = (
    re.compile(
        r"/player-id/([^/?#!]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"/userid/([^/?#!]+)",
        re.IGNORECASE,
    ),
)


def clean_text(
    value: str,
) -> str:
    return " ".join(
        value.replace("\xa0", " ").split()
    )


def extract_external_id(
    href: str,
) -> str | None:
    for pattern in PLAYER_ID_PATTERNS:
        match = pattern.search(href)

        if match:
            return match.group(1).strip()

    return None


def extract_minute(
    row,
) -> int | None:
    time_node = row.select_one(
        ".column-time"
    )

    if time_node is None:
        return None

    text = clean_text(
        time_node.get_text(
            " ",
            strip=True,
        )
    )

    match = re.search(
        r"\b(\d{1,3})\b",
        text,
    )

    if match is None:
        return None

    return int(
        match.group(1)
    )


def get_player_links(
    row,
) -> list[dict]:
    result: list[dict] = []

    for link in row.select(
        "a[href*='/spielerprofil/']"
    ):
        href = str(
            link.get(
                "href",
                "",
            )
        )

        external_id = extract_external_id(
            href
        )

        text = clean_text(
            link.get_text(
                " ",
                strip=True,
            )
        )

        result.append(
            {
                "external_id": external_id,
                "href": href,
                "text": text,
            }
        )

    return result


def row_classes(
    row,
) -> str:
    return " ".join(
        row.get(
            "class",
            [],
        )
    )


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 73 RAW-HTML-DIAGNOSE / "
        "FINN KONRAD 71' UND 86'"
    )
    print("=" * 110)

    if not HTML_PATH.exists():
        raise FileNotFoundError(
            f"HTML fehlt: {HTML_PATH}"
        )

    html = HTML_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    print(f"HTML: {HTML_PATH}")
    print(
        f"Größe: {len(html)} Zeichen"
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    rows = soup.select(
        ".row-event"
    )

    print(
        f"Gefundene Event-Zeilen: "
        f"{len(rows)}"
    )

    target_rows: list[
        tuple[int, object, list[dict]]
    ] = []

    finn_occurrences = 0

    for row in rows:
        minute = extract_minute(
            row
        )

        links = get_player_links(
            row
        )

        ids = {
            link["external_id"]
            for link in links
            if link["external_id"]
        }

        if ids & FINN_EXTERNAL_IDS:
            finn_occurrences += 1

        if minute in TARGET_MINUTES:
            target_rows.append(
                (
                    minute,
                    row,
                    links,
                )
            )

    print()
    print("FINN-ID")
    print("-" * 110)

    for external_id in sorted(
        FINN_EXTERNAL_IDS
    ):
        print(
            f"{external_id} | "
            f"HTML-Vorkommen="
            f"{html.count(external_id)}"
        )

    print(
        f"Event-Zeilen mit Finn-ID: "
        f"{finn_occurrences}"
    )

    print()
    print("EVENT-ZEILEN 71' / 86'")
    print("=" * 110)

    if not target_rows:
        print("(keine)")
    else:
        for minute, row, links in target_rows:
            print()
            print("-" * 110)
            print(
                f"MINUTE {minute}' | "
                f"Klassen: {row_classes(row)}"
            )
            print("-" * 110)

            row_text = clean_text(
                row.get_text(
                    " ",
                    strip=True,
                )
            )

            print(
                f"TEXT: {row_text}"
            )

            print("SPIELER-LINKS:")

            if not links:
                print("  (keine)")
            else:
                for index, link in enumerate(
                    links,
                    start=1,
                ):
                    marker = (
                        " <-- FINN"
                        if link["external_id"]
                        in FINN_EXTERNAL_IDS
                        else ""
                    )

                    print(
                        f"  [{index}] "
                        f"external_id="
                        f"{link['external_id']} "
                        f"text={link['text']!r}"
                        f"{marker}"
                    )
                    print(
                        f"      href="
                        f"{link['href']}"
                    )

            print()
            print("RAW HTML:")
            print(
                row.prettify()
            )

    print()
    print("=" * 110)
    print("AUSWERTUNG")
    print("=" * 110)

    finn_target_rows = []

    for minute, row, links in target_rows:
        finn_in_row = any(
            link["external_id"]
            in FINN_EXTERNAL_IDS
            for link in links
        )

        if finn_in_row:
            finn_target_rows.append(
                minute
            )

    print(
        "Finn-ID in Zielminuten gefunden: "
        f"{sorted(finn_target_rows)}"
    )

    if (
        71 in finn_target_rows
        and 86 in finn_target_rows
    ):
        print()
        print(
            "BEFUND: Die Finn-Konrad-ID steht "
            "bereits im gespeicherten Roh-HTML "
            "sowohl beim 71'- als auch beim "
            "86'-Wechsel."
        )
        print(
            "Dann ist die Doppel-Einwechslung "
            "quellseitig bzw. bereits im "
            "gespeicherten FUSSBALL.DE-HTML "
            "vorhanden und kein EventMapper-Fehler."
        )
    else:
        print()
        print(
            "BEFUND: Die beiden Wechsel sind im "
            "Roh-HTML nicht identisch abgebildet."
        )
        print(
            "Dann müssen Parser/ID-Auflösung "
            "noch einmal geprüft werden."
        )

    print("=" * 110)


if __name__ == "__main__":
    main()
