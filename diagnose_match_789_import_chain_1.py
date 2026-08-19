from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.importer.fussballde.liveticker_parser import (
    LivetickerParser,
)
from src.importer.fussballde.match_event_importer import (
    MatchEventImporter,
)
from src.importer.fussballde.parsers.match_detail_parser import (
    MatchDetailParser,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)

EXTERNAL_MATCH_ID = (
    "031BG6B7PG000000VS5489BUVUR5FS5A"
)

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "fc-energie-cottbus-hannover-96/-/spiel/"
    f"{EXTERNAL_MATCH_ID}#!/"
)

HTML_PATH = Path(
    "debug/html/matches"
) / f"{EXTERNAL_MATCH_ID}.html"

JSON_PATH = Path(
    "debug/liveticker/json"
) / f"{EXTERNAL_MATCH_ID}.json"

GOAL_CODES = {
    "GOAL",
    "OWN_GOAL",
    "PENALTY_GOAL",
}


def get_match_row(
    connection: sqlite3.Connection,
) -> sqlite3.Row:
    connection.row_factory = sqlite3.Row

    row = connection.execute(
        """
        SELECT *
        FROM matches
        WHERE external_id = ?
        LIMIT 1
        """,
        (EXTERNAL_MATCH_ID,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "Spiel wurde in der Datenbank "
            "nicht gefunden."
        )

    return row


def get_team_ids(
    row: sqlite3.Row,
) -> tuple[int, int]:
    keys = set(row.keys())

    home_candidates = (
        "home_team_id",
        "team_home_id",
        "home_id",
    )
    away_candidates = (
        "away_team_id",
        "team_away_id",
        "away_id",
    )

    home_team_id = next(
        (
            row[name]
            for name in home_candidates
            if name in keys
            and row[name] is not None
        ),
        None,
    )

    away_team_id = next(
        (
            row[name]
            for name in away_candidates
            if name in keys
            and row[name] is not None
        ),
        None,
    )

    if (
        home_team_id is None
        or away_team_id is None
    ):
        raise RuntimeError(
            "Heim-/Auswärts-Team-ID konnte "
            "nicht aus matches ermittelt werden. "
            f"Vorhandene Spalten: {sorted(keys)}"
        )

    return (
        int(home_team_id),
        int(away_team_id),
    )


def load_detail_data():
    if not HTML_PATH.exists():
        raise FileNotFoundError(
            f"HTML fehlt: {HTML_PATH}"
        )

    html = HTML_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    parser = MatchDetailParser(None)

    return parser.parse(
        html=html,
        source_url=MATCH_URL,
    )


def load_liveticker_data():
    if not JSON_PATH.exists():
        raise FileNotFoundError(
            f"JSON fehlt: {JSON_PATH}"
        )

    raw = JSON_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    payload = json.loads(raw)

    parser = LivetickerParser()

    return parser.parse_auto(
        content=payload,
        match_id=EXTERNAL_MATCH_ID,
    )


def count_parser_goals(
    liveticker_data,
) -> int:
    return sum(
        1
        for event in liveticker_data.events
        if event.event_type in {
            "goal",
            "own_goal",
            "penalty_goal",
        }
    )


def get_db_events(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            events.event_id,
            event_types.code AS event_type_code,
            events.minute,
            events.second,
            events.team_id,
            events.player_id,
            events.value,
            events.notes
        FROM events
        INNER JOIN event_types
            ON event_types.event_type_id =
               events.event_type_id
        WHERE events.match_id = ?
        ORDER BY
            events.minute,
            events.second,
            events.event_id
        """,
        (match_id,),
    ).fetchall()


def count_db_goals(
    rows: list[sqlite3.Row],
) -> int:
    return sum(
        1
        for row in rows
        if str(
            row["event_type_code"]
        ).upper() in GOAL_CODES
    )


def print_goal_events(
    title: str,
    rows: list[sqlite3.Row],
) -> None:
    print()
    print(title)
    print("-" * 100)

    goals = [
        row
        for row in rows
        if str(
            row["event_type_code"]
        ).upper() in GOAL_CODES
    ]

    if not goals:
        print("Keine Tor-Events.")
        return

    for row in goals:
        print(
            f"event_id={row['event_id']:<5} | "
            f"{row['minute']}' | "
            f"{row['event_type_code']:<14} | "
            f"team_id={row['team_id']} | "
            f"player_id={row['player_id']} | "
            f"{row['notes']}"
        )


def main() -> None:
    print("=" * 100)
    print(
        "DIAGNOSE IMPORTKETTE "
        "COTTBUS - HANNOVER"
    )
    print("=" * 100)

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        match_row = get_match_row(
            connection
        )

        match_id = int(
            match_row["match_id"]
        )

        home_team_id, away_team_id = (
            get_team_ids(match_row)
        )

        print(
            f"DB match_id:       {match_id}"
        )
        print(
            f"Externe Spiel-ID:  "
            f"{EXTERNAL_MATCH_ID}"
        )
        print(
            f"Team-IDs:          "
            f"{home_team_id} / {away_team_id}"
        )

        before = get_db_events(
            connection,
            match_id,
        )

        print()
        print(
            "DB VORHER"
        )
        print(
            f"Events insgesamt:   {len(before)}"
        )
        print(
            f"Tor-Events:         "
            f"{count_db_goals(before)}"
        )

        print_goal_events(
            "TOR-EVENTS VORHER",
            before,
        )

        detail_data = load_detail_data()
        liveticker_data = (
            load_liveticker_data()
        )

        print()
        print(
            "PARSER"
        )
        print("-" * 100)
        print(
            f"HTML:               "
            f"{detail_data.home_team} - "
            f"{detail_data.away_team}"
        )
        print(
            f"Liveticker Events:  "
            f"{len(liveticker_data.events)}"
        )
        print(
            f"Liveticker Tore:    "
            f"{count_parser_goals(liveticker_data)}"
        )

        importer = MatchEventImporter(
            connection
        )

        prepared_events: list[dict] = []

        for event in liveticker_data.events:
            team_id = (
                importer
                ._resolve_liveticker_team_id(
                    match_id=match_id,
                    event=event,
                    detail_data=detail_data,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                )
            )

            if event.event_type == "substitution":
                prepared_events.extend(
                    importer
                    ._prepare_liveticker_substitution(
                        event=event,
                        team_id=team_id,
                    )
                )
                continue

            prepared = (
                importer
                ._prepare_liveticker_event(
                    match_id=match_id,
                    event=event,
                    team_id=team_id,
                )
            )

            if prepared is not None:
                prepared_events.append(
                    prepared
                )

        prepared_goals = sum(
            1
            for event in prepared_events
            if str(
                event.get(
                    "event_type_code",
                    "",
                )
            ).upper() in GOAL_CODES
        )

        print()
        print(
            "PREPARED EVENTS"
        )
        print("-" * 100)
        print(
            f"Events vorbereitet: {len(prepared_events)}"
        )
        print(
            f"Tore vorbereitet:   {prepared_goals}"
        )

        print()
        print(
            "IMPORT"
        )
        print("-" * 100)

        imported_count, player_ids = (
            importer.import_events(
                match_id=match_id,
                detail_data=detail_data,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                liveticker_data=liveticker_data,
            )
        )

        print(
            f"Events geschrieben: {imported_count}"
        )
        print(
            f"Spieler berührt:    {len(player_ids)}"
        )

        after = get_db_events(
            connection,
            match_id,
        )

        print()
        print(
            "DB NACHHER"
        )
        print("-" * 100)
        print(
            f"Events insgesamt:   {len(after)}"
        )
        print(
            f"Tor-Events:         "
            f"{count_db_goals(after)}"
        )

        print_goal_events(
            "TOR-EVENTS NACHHER",
            after,
        )

        print()
        print("=" * 100)

        parser_goals = (
            count_parser_goals(
                liveticker_data
            )
        )
        db_goals = count_db_goals(
            after
        )

        if (
            parser_goals
            == prepared_goals
            == db_goals
        ):
            print(
                "ERGEBNIS: Kette ist konsistent "
                f"({db_goals} Tor-Events)."
            )
        else:
            print(
                "ERGEBNIS: Abweichung gefunden!"
            )
            print(
                f"Parser:   {parser_goals}"
            )
            print(
                f"Prepared: {prepared_goals}"
            )
            print(
                f"DB:       {db_goals}"
            )

        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()