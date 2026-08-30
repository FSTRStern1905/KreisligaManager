from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.match_detail_importer import MatchDetailImporter


SOURCE_DB = Path("data/database/kreisligamanager.db")
TEST_DB = Path("data/database/match_131_reimport_test.db")

MATCH_EXTERNAL_ID = "02TNB07I8O000000VS5489BUVSSD35NB"

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "vfl-trier-sg-weintal-oberemmel/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)

EXPECTED_EVENTS = [
    ("024GQEO9HK000000VS541L4HVV6K67AP", "Maurice", "Mertz", 56),
    ("02S1FR2ELC000000VS5489B7VTPM6DDT", "Matheus", "Ramos Maciel", 59),
    ("01O947N4B4000000VS541L4GVUTRMLKN", "Rene Harald", "Fischer", 64),
    ("02JEB55S6K000000VUM1DNR4VSGLGJKE", "Theo", "Faber", 64),
    ("00L549Q0EC000000VV0AG85VVV79K56V", "Torben", "Weber", 73),
    ("023R8DFVB4000000VS541L4HVS74CJKC", "Christoph", "Weiland", 81),
]


def get_target_rows(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    external_ids = [item[0] for item in EXPECTED_EVENTS]
    placeholders = ",".join("?" for _ in external_ids)

    return connection.execute(
        f"""
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.team_id,
            e.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            e.related_player_id
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        WHERE
            e.match_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
            AND (
                p.external_id IN ({placeholders})
                OR EXISTS (
                    SELECT 1
                    FROM player_external_ids AS pei
                    WHERE pei.player_id = p.player_id
                      AND pei.external_id IN ({placeholders})
                )
            )
        ORDER BY e.minute, e.event_id
        """,
        (match_id, *external_ids, *external_ids),
    ).fetchall()


def player_has_external_id(
    connection: sqlite3.Connection,
    player_id: int,
    external_id: str,
) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM players AS p
        WHERE p.player_id = ?
          AND (
              p.external_id = ?
              OR EXISTS (
                  SELECT 1
                  FROM player_external_ids AS pei
                  WHERE pei.player_id = p.player_id
                    AND pei.external_id = ?
              )
          )
        LIMIT 1
        """,
        (player_id, external_id, external_id),
    ).fetchone()

    return row is not None


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


def validate_expected_events(
    connection: sqlite3.Connection,
    rows: list[sqlite3.Row],
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    for external_id, first_name, last_name, minute in EXPECTED_EVENTS:
        matches = [
            row
            for row in rows
            if row["player_id"] is not None
            and player_has_external_id(
                connection,
                int(row["player_id"]),
                external_id,
            )
        ]

        if len(matches) != 1:
            errors.append(
                f"{minute}' {first_name} {last_name}: "
                f"{len(matches)} passende Events statt 1."
            )
            continue

        row = matches[0]

        if row["code"] != "SUBSTITUTION_OUT":
            errors.append(
                f"{minute}' {first_name} {last_name}: "
                f"{row['code']} statt SUBSTITUTION_OUT."
            )

        if int(row["minute"] or 0) != minute:
            errors.append(
                f"{first_name} {last_name}: "
                f"Minute {row['minute']} statt {minute}."
            )

        if row["related_player_id"] is not None:
            errors.append(
                f"{minute}' {first_name} {last_name}: "
                "related_player_id ist nicht NULL."
            )

    return not errors, errors


def main() -> None:
    print("=" * 94)
    print("SPIEL 131 REIMPORT-TEST / 6 EINSEITIGE AUSWECHSLUNGEN")
    print("=" * 94)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {SOURCE_DB}"
        )

    shutil.copy2(
        SOURCE_DB,
        TEST_DB,
    )

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
                "Spiel 131 wurde nicht gefunden."
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

        valid_events, event_errors = validate_expected_events(
            connection,
            after,
        )

        home_team_id = int(match["home_team_id"])
        away_team_id = int(match["away_team_id"])

        valid_starters = (
            starter_counts.get(home_team_id) == 11
            and starter_counts.get(away_team_id) == 11
        )

        print()
        print("=" * 94)

        if valid_events and valid_starters:
            connection.commit()
            print(
                "ERGEBNIS: SPIEL 131 REIMPORT SAUBER."
            )
            print(
                "Alle 6 einseitigen Auswechslungen wurden als "
                "SUBSTITUTION_OUT mit related_player_id=NULL importiert."
            )
        else:
            connection.rollback()
            print(
                "ERGEBNIS: SPIEL 131 NOCH NICHT SAUBER."
            )
            print(
                "Test-DB wurde zurückgerollt."
            )

            for error in event_errors:
                print(f"Fehler: {error}")

            if not valid_starters:
                print(
                    "Fehler: Starterprüfung nicht bestanden."
                )

            raise RuntimeError(
                "Qualitätsprüfung für Spiel 131 "
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
