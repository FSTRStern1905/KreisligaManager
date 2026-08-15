from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.importer.fussballde.liveticker_parser import (
    LivetickerParser,
)
from src.importer.fussballde.match_detail_importer import (
    MatchDetailImporter,
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


def load_detail_data():
    html = HTML_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    return MatchDetailParser(None).parse(
        html=html,
        source_url=MATCH_URL,
    )


def load_liveticker_data():
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


def get_db_result(
    connection: sqlite3.Connection,
):
    return connection.execute(
        """
        SELECT
            match_id,
            home_goals,
            away_goals,
            status,
            detail_imported
        FROM matches
        WHERE external_id = ?
        LIMIT 1
        """,
        (EXTERNAL_MATCH_ID,),
    ).fetchone()


def main() -> None:
    print("=" * 100)
    print("DIAGNOSE MATCHDETAIL-RESULT-FALLBACK")
    print("=" * 100)

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        before = get_db_result(
            connection
        )

        print()
        print("DB VORHER")
        print("-" * 100)
        print(
            f"match_id:        {before['match_id']}"
        )
        print(
            f"Ergebnis:        "
            f"{before['home_goals']}:"
            f"{before['away_goals']}"
        )
        print(
            f"Status:          {before['status']}"
        )
        print(
            f"detail_imported: {before['detail_imported']}"
        )

        detail_data = load_detail_data()
        liveticker_data = load_liveticker_data()

        print()
        print("DETAILDATA VOR FALLBACK")
        print("-" * 100)
        print(
            f"Ergebnis: "
            f"{detail_data.home_goals}:"
            f"{detail_data.away_goals}"
        )

        importer = MatchDetailImporter(
            connection
        )

        importer._fill_result_from_liveticker(
            detail_data=detail_data,
            liveticker_data=liveticker_data,
        )

        print()
        print("DETAILDATA NACH FALLBACK")
        print("-" * 100)
        print(
            f"Ergebnis: "
            f"{detail_data.home_goals}:"
            f"{detail_data.away_goals}"
        )

        print()
        print("IMPORT_DATA")
        print("-" * 100)

        result = importer.import_data(
            detail_data=detail_data,
            source_url=MATCH_URL,
            liveticker_data=liveticker_data,
        )

        print(
            f"match_id:                  "
            f"{result.get('match_id')}"
        )
        print(
            f"home_goals:                "
            f"{result.get('home_goals')}"
        )
        print(
            f"away_goals:                "
            f"{result.get('away_goals')}"
        )
        print(
            f"events_imported:           "
            f"{result.get('events_imported')}"
        )
        print(
            f"player_match_stats_created:"
            f" {result.get('player_match_stats_created')}"
        )

        after = get_db_result(
            connection
        )

        print()
        print("DB NACHHER")
        print("-" * 100)
        print(
            f"Ergebnis:        "
            f"{after['home_goals']}:"
            f"{after['away_goals']}"
        )
        print(
            f"Status:          {after['status']}"
        )
        print(
            f"detail_imported: {after['detail_imported']}"
        )

        print()
        print("=" * 100)

        if (
            after["home_goals"] == 4
            and after["away_goals"] == 1
        ):
            print(
                "ERGEBNIS: Fallback + DB-Update funktionieren."
            )
        else:
            print(
                "ERGEBNIS: Ergebnis wurde noch nicht korrekt "
                "in matches geschrieben."
            )

        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
