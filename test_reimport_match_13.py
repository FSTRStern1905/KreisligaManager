from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.match_detail_importer import MatchDetailImporter


SOURCE_DB = Path("data/database/kreisligamanager.db")
TEST_DB = Path("data/database/match_13_reimport_test.db")

MATCH_EXTERNAL_ID = "02TNB07CG0000000VS5489BUVSSD35NB"

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "djk-st-matthias-trier-sg-serrig/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)

TARGET_PLAYER_EXTERNAL_ID = "00L54A59RO000000VV0AG85VVV79K56V"


def get_target_rows(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.team_id,
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        WHERE
            e.match_id = ?
            AND (
                p.external_id = ?
                OR EXISTS (
                    SELECT 1
                    FROM player_external_ids AS pei
                    WHERE pei.player_id = p.player_id
                      AND pei.external_id = ?
                )
            )
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY e.minute, e.event_id
        """,
        (
            match_id,
            TARGET_PLAYER_EXTERNAL_ID,
            TARGET_PLAYER_EXTERNAL_ID,
        ),
    ).fetchall()


def main() -> None:
    print("=" * 94)
    print("SPIEL 13 REIMPORT-TEST / EINSEITIGE AUSWECHSLUNG")
    print("=" * 94)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {SOURCE_DB}"
        )

    shutil.copy2(SOURCE_DB, TEST_DB)

    print(f"Quelle:  {SOURCE_DB}")
    print(f"Test-DB: {TEST_DB}")
    print("Haupt-DB wird NICHT verändert.")

    connection = sqlite3.connect(TEST_DB)
    connection.row_factory = sqlite3.Row

    browser = FussballDeBrowser()

    try:
        match = connection.execute(
            """
            SELECT
                match_id,
                matchday,
                home_team_id,
                away_team_id
            FROM matches
            WHERE external_id = ?
            LIMIT 1
            """,
            (MATCH_EXTERNAL_ID,),
        ).fetchone()

        if match is None:
            raise RuntimeError(
                "Spiel 13 wurde nicht gefunden."
            )

        match_id = int(match["match_id"])

        print()
        print("MATCH")
        print("-" * 94)
        print(dict(match))

        before = get_target_rows(
            connection,
            match_id,
        )

        print()
        print("VOR REIMPORT")
        print("-" * 94)
        for row in before:
            print(dict(row))

        browser.start(headless=False)

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht erstellt werden."
            )

        importer = MatchDetailImporter(connection)

        result = importer.import_from_page(
            page=browser.page,
            source_url=MATCH_URL,
        )

        print()
        print("IMPORTERGEBNIS")
        print("-" * 94)
        print(
            "lineups_imported: "
            f"{result.get('lineups_imported')}"
        )
        print(
            "events_imported:  "
            f"{result.get('events_imported')}"
        )
        print(
            "event_source:     "
            f"{result.get('event_source')}"
        )

        after = get_target_rows(
            connection,
            match_id,
        )

        print()
        print("NACH REIMPORT")
        print("-" * 94)
        for row in after:
            print(dict(row))

        valid = (
            len(after) == 1
            and after[0]["code"] == "SUBSTITUTION_OUT"
            and int(after[0]["minute"] or 0) == 0
            and after[0]["related_player_id"] is None
            and after[0]["first_name"] == "Slawa"
            and after[0]["last_name"] == "Sauer"
        )

        print()
        print("=" * 94)

        if valid:
            connection.commit()
            print(
                "ERGEBNIS: EINSEITIGE AUSWECHSLUNG "
                "WIRD KORREKT IMPORTIERT."
            )
            print(
                "0' SUBSTITUTION_OUT Slawa Sauer "
                "mit related_player_id=NULL."
            )
        else:
            connection.rollback()
            print(
                "ERGEBNIS: SPIEL 13 NOCH NICHT SAUBER."
            )
            print(
                "Erwartet wird genau ein 0'-Event: "
                "SUBSTITUTION_OUT Slawa Sauer."
            )

        print("=" * 94)

        if not valid:
            raise RuntimeError(
                "Qualitätsprüfung für Spiel 13 "
                "nicht bestanden."
            )

    except Exception:
        connection.rollback()
        raise

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()
