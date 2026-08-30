from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.match_detail_importer import (
    MatchDetailImporter,
)


SOURCE_DB = Path(
    "data/database/kreisligamanager.db"
)
TEST_DB = Path(
    "data/database/match_260_reimport_test.db"
)

MATCH_EXTERNAL_ID = (
    "02TKDR1VGS000000VS5489BUVUD1610F"
)

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "1-fc-union-berlin-sport-club-freiburg/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)

EXPECTED_AWAY_TEAM_ID = 28


def get_substitution_rows(
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
            ON et.event_type_id =
               e.event_type_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        WHERE
            e.match_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY
            e.minute,
            e.event_id
        """,
        (match_id,),
    ).fetchall()


def main() -> None:
    print("=" * 94)
    print("SPIEL 260 REIMPORT-TEST")
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

    connection = sqlite3.connect(
        TEST_DB
    )
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
                "Spiel 260 wurde nicht gefunden."
            )

        match_id = int(
            match["match_id"]
        )

        print()
        print("MATCH")
        print("-" * 94)
        print(dict(match))

        before = get_substitution_rows(
            connection,
            match_id,
        )

        before_teamless = sum(
            1
            for row in before
            if row["team_id"] is None
        )

        print()
        print("VOR REIMPORT")
        print("-" * 94)
        print(
            f"Wechsel-Events gesamt: {len(before)}"
        )
        print(
            f"Ohne team_id:          {before_teamless}"
        )

        browser.start(
            headless=False,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht erstellt werden."
            )

        importer = MatchDetailImporter(
            connection
        )

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

        after = get_substitution_rows(
            connection,
            match_id,
        )

        after_teamless = sum(
            1
            for row in after
            if row["team_id"] is None
        )

        print()
        print("NACH REIMPORT")
        print("-" * 94)
        print(
            f"Wechsel-Events gesamt: {len(after)}"
        )
        print(
            f"Ohne team_id:          {after_teamless}"
        )

        target_rows = [
            row
            for row in after
            if (
                (
                    row["first_name"] == "Lucas"
                    and row["last_name"] == "Höler"
                )
                or (
                    row["first_name"] == "Nicolas"
                    and row["last_name"] == "Höfler"
                )
            )
        ]

        print()
        print("HÖLER / HÖFLER")
        print("-" * 94)

        for row in target_rows:
            print(dict(row))

        starter_rows = connection.execute(
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

        starter_counts = {
            int(row["team_id"]): int(
                row["starters"] or 0
            )
            for row in starter_rows
            if row["team_id"] is not None
        }

        print()
        print("STARTER")
        print("-" * 94)
        print(starter_counts)

        valid_target_rows = (
            len(target_rows) == 2
            and all(
                int(row["team_id"] or 0)
                == EXPECTED_AWAY_TEAM_ID
                for row in target_rows
            )
        )

        valid = (
            len(after) == 18
            and after_teamless == 0
            and valid_target_rows
            and starter_counts.get(17) == 11
            and starter_counts.get(28) == 11
        )

        print()
        print("=" * 94)

        if valid:
            connection.commit()
            print(
                "ERGEBNIS: SPIEL 260 REIMPORT SAUBER."
            )
            print(
                "Lucas Höler und Nicolas Höfler "
                "haben team_id=28."
            )
        else:
            connection.rollback()
            print(
                "ERGEBNIS: SPIEL 260 NOCH NICHT SAUBER."
            )
            print(
                "Test-DB wurde zurückgerollt."
            )

        print("=" * 94)

        if not valid:
            raise RuntimeError(
                "Qualitätsprüfung für Spiel 260 "
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
