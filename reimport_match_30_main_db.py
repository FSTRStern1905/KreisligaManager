from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.match_detail_importer import MatchDetailImporter


DB_PATH = Path("data/database/kreisligamanager.db")
BACKUP_DIR = Path("data/database/backups")

MATCH_EXTERNAL_ID = "02TNB07D30000000VS5489BUVSSD35NB"

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "vfl-trier-sg-kenn/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)

TARGET_PLAYER_EXTERNAL_ID = "015OCUSE2S000000VV0AG811VS5HGDVH"
EXPECTED_TEAM_ID = 6


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


def get_starter_counts(
    connection: sqlite3.Connection,
    match_id: int,
) -> dict[int, int]:
    rows = connection.execute(
        """
        SELECT
            team_id,
            SUM(
                CASE
                    WHEN is_starting = 1
                    THEN 1
                    ELSE 0
                END
            ) AS starters
        FROM player_match_stats
        WHERE match_id = ?
        GROUP BY team_id
        ORDER BY team_id
        """,
        (match_id,),
    ).fetchall()

    return {
        int(row["team_id"]): int(row["starters"] or 0)
        for row in rows
        if row["team_id"] is not None
    }


def main() -> None:
    print("=" * 94)
    print("HAUPT-DB REIMPORT: SPIEL 30")
    print("=" * 94)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {DB_PATH}"
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = BACKUP_DIR / (
        "kreisligamanager_before_match_30_"
        f"{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    print(f"Haupt-DB: {DB_PATH}")
    print(f"Backup:   {backup_path}")
    print("Es wird ausschließlich Spiel 30 reimportiert.")

    connection = sqlite3.connect(DB_PATH)
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
                "Spiel 30 wurde nicht gefunden."
            )

        match_id = int(match["match_id"])
        home_team_id = int(match["home_team_id"])
        away_team_id = int(match["away_team_id"])

        print()
        print("MATCH")
        print("-" * 94)
        print(dict(match))

        print()
        print("VOR REIMPORT")
        print("-" * 94)

        before = get_target_rows(
            connection,
            match_id,
        )

        for row in before:
            print(dict(row))

        connection.execute(
            "BEGIN IMMEDIATE"
        )

        browser.start(
            headless=False,
        )

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

        starter_counts = get_starter_counts(
            connection,
            match_id,
        )

        print()
        print("STARTER")
        print("-" * 94)
        print(starter_counts)

        valid_target = (
            len(after) == 1
            and after[0]["code"] == "SUBSTITUTION_OUT"
            and int(after[0]["minute"] or 0) == 90
            and int(after[0]["team_id"] or 0) == EXPECTED_TEAM_ID
            and after[0]["related_player_id"] is None
            and after[0]["first_name"] == "Jan"
            and after[0]["last_name"] == "Wagner"
        )

        valid_starters = (
            starter_counts.get(home_team_id) == 11
            and starter_counts.get(away_team_id) == 11
        )

        print()
        print("=" * 94)

        if valid_target and valid_starters:
            connection.commit()
            print(
                "ERGEBNIS: SPIEL 30 REIMPORT ERFOLGREICH."
            )
            print(
                "Änderungen wurden in die Haupt-DB übernommen."
            )
            print(
                "90' SUBSTITUTION_OUT Jan Wagner "
                "mit related_player_id=NULL."
            )
        else:
            connection.rollback()
            print(
                "ERGEBNIS: SPIEL 30 REIMPORT FEHLGESCHLAGEN."
            )
            print(
                "Transaktion wurde zurückgerollt."
            )

            if not valid_target:
                print(
                    "Fehler: Jan-Wagner-Ereignis "
                    "ist nicht korrekt."
                )

            if not valid_starters:
                print(
                    "Fehler: Starterprüfung "
                    "nicht bestanden."
                )

            raise RuntimeError(
                "Qualitätsprüfung für Spiel 30 "
                "nicht bestanden."
            )

        print("=" * 94)

    except Exception:
        connection.rollback()
        raise

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()
