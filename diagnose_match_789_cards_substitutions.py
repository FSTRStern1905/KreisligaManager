from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.importer.fussballde.liveticker_parser import (
    LivetickerParser,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

MATCH_ID = 789

EXTERNAL_MATCH_ID = (
    "031BG6B7PG000000VS5489BUVUR5FS5A"
)

JSON_PATH = Path(
    "debug/liveticker/json"
) / f"{EXTERNAL_MATCH_ID}.json"

INTERESTING_TYPES = {
    "YELLOW_CARD",
    "YELLOW_RED_CARD",
    "RED_CARD",
    "SUBSTITUTION_IN",
    "SUBSTITUTION_OUT",
}


def load_liveticker():
    payload = json.loads(
        JSON_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    return LivetickerParser().parse_auto(
        content=payload,
        match_id=EXTERNAL_MATCH_ID,
    )


def print_parser_events(
    liveticker_data,
) -> None:
    print("=" * 100)
    print("PARSER: KARTEN + WECHSEL")
    print("=" * 100)

    count = 0

    for event in liveticker_data.events:
        if event.event_type not in {
            "yellow_card",
            "yellow_red_card",
            "red_card",
            "substitution",
        }:
            continue

        count += 1

        print(
            f"{count:>2}. "
            f"{event.minute}' | "
            f"{event.event_type:<16} | "
            f"team_ext={event.team or '-'}"
        )

        print(
            f"    Spieler: "
            f"{event.player or '-'} "
            f"[{event.player_id or '-'}]"
        )

        if event.event_type == "substitution":
            print(
                f"    Spieler 2: "
                f"{event.player_out or '-'} "
                f"[{event.player_out_id or '-'}]"
            )

        print(
            f"    {event.description}"
        )
        print()

    print(
        f"Parser-Ereignisse geprüft: {count}"
    )
    print()


def print_db_events(
    connection: sqlite3.Connection,
) -> None:
    print("=" * 100)
    print("DATENBANK: KARTEN + WECHSEL")
    print("=" * 100)

    rows = connection.execute(
        """
        SELECT
            events.event_id,
            event_types.code AS event_type_code,
            events.minute,
            events.team_id,
            events.player_id,
            events.related_player_id,
            events.notes,
            p1.first_name AS player_first_name,
            p1.last_name AS player_last_name,
            p2.first_name AS related_first_name,
            p2.last_name AS related_last_name
        FROM events
        INNER JOIN event_types
            ON event_types.event_type_id =
               events.event_type_id
        LEFT JOIN players AS p1
            ON p1.player_id =
               events.player_id
        LEFT JOIN players AS p2
            ON p2.player_id =
               events.related_player_id
        WHERE
            events.match_id = ?
            AND event_types.code IN (
                'YELLOW_CARD',
                'YELLOW_RED_CARD',
                'RED_CARD',
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY
            events.minute,
            events.event_id
        """,
        (MATCH_ID,),
    ).fetchall()

    errors = 0

    for index, row in enumerate(
        rows,
        start=1,
    ):
        player_name = " ".join(
            part
            for part in (
                row["player_first_name"] or "",
                row["player_last_name"] or "",
            )
            if part
        ) or "-"

        related_name = " ".join(
            part
            for part in (
                row["related_first_name"] or "",
                row["related_last_name"] or "",
            )
            if part
        ) or "-"

        print(
            f"{index:>2}. "
            f"{row['minute']}' | "
            f"{row['event_type_code']:<18} | "
            f"team_id={row['team_id']} | "
            f"player_id={row['player_id']} "
            f"({player_name}) | "
            f"related={row['related_player_id']} "
            f"({related_name})"
        )

        print(
            f"    {row['notes'] or ''}"
        )

        if row["team_id"] is None:
            errors += 1
            print(
                "    !!! FEHLER: team_id fehlt"
            )

        if row["player_id"] is None:
            errors += 1
            print(
                "    !!! FEHLER: player_id fehlt"
            )

        if (
            row["event_type_code"]
            in {
                "SUBSTITUTION_IN",
                "SUBSTITUTION_OUT",
            }
            and row["related_player_id"] is None
        ):
            errors += 1
            print(
                "    !!! FEHLER: related_player_id fehlt"
            )

        print()

    print(
        f"DB-Ereignisse geprüft: {len(rows)}"
    )
    print(
        f"Zuordnungsfehler:      {errors}"
    )
    print()

    print("=" * 100)

    if errors == 0:
        print(
            "ERGEBNIS: Karten und Wechsel "
            "sind vollständig zugeordnet."
        )
    else:
        print(
            "ERGEBNIS: Es gibt noch "
            f"{errors} Zuordnungsfehler."
        )

    print("=" * 100)


def main() -> None:
    print("=" * 100)
    print(
        "DIAGNOSE KARTEN + WECHSEL "
        "COTTBUS - HANNOVER"
    )
    print("=" * 100)
    print()

    liveticker_data = load_liveticker()

    print_parser_events(
        liveticker_data
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        print_db_events(
            connection
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
