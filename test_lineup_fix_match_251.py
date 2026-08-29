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
    "data/database/alias_fix_test.db"
)

MATCH_EXTERNAL_ID = (
    "02TKDR1UT8000000VS5489BUVUD1610F"
)

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "borussia-moenchengladbach-fc-bayern-muenchen/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)


def count_mapping_problems(
    connection: sqlite3.Connection,
    match_id: int,
) -> tuple[int, int]:
    rows = connection.execute(
        """
        SELECT DISTINCT
            e.player_id
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id =
               e.event_type_id
        WHERE
            e.match_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
            AND e.player_id IS NOT NULL
        """,
        (match_id,),
    ).fetchall()

    event_players = len(rows)
    missing_in_lineup = 0

    for row in rows:
        player_id = int(row["player_id"])

        exists = connection.execute(
            """
            SELECT 1
            FROM lineups
            WHERE
                match_id = ?
                AND player_id = ?
            LIMIT 1
            """,
            (
                match_id,
                player_id,
            ),
        ).fetchone()

        if exists is None:
            missing_in_lineup += 1

    return (
        event_players,
        missing_in_lineup,
    )


def print_team_quality(
    connection: sqlite3.Connection,
    match_id: int,
) -> None:
    teams = connection.execute(
        """
        SELECT
            m.home_team_id AS team_id,
            ht.name AS team_name
        FROM matches AS m
        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id
        WHERE m.match_id = ?

        UNION ALL

        SELECT
            m.away_team_id AS team_id,
            at.name AS team_name
        FROM matches AS m
        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id
        WHERE m.match_id = ?
        """,
        (
            match_id,
            match_id,
        ),
    ).fetchall()

    for team in teams:
        team_id = int(team["team_id"])

        event_counts = connection.execute(
            """
            SELECT
                SUM(
                    CASE
                        WHEN et.code =
                             'SUBSTITUTION_IN'
                        THEN 1
                        ELSE 0
                    END
                ) AS in_count,
                SUM(
                    CASE
                        WHEN et.code =
                             'SUBSTITUTION_OUT'
                        THEN 1
                        ELSE 0
                    END
                ) AS out_count
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id =
                   e.event_type_id
            WHERE
                e.match_id = ?
                AND e.team_id = ?
            """,
            (
                match_id,
                team_id,
            ),
        ).fetchone()

        stats_counts = connection.execute(
            """
            SELECT
                SUM(
                    CASE
                        WHEN was_substituted_in = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS in_count,
                SUM(
                    CASE
                        WHEN was_substituted_out = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS out_count,
                SUM(
                    CASE
                        WHEN is_starting = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS starters
            FROM player_match_stats
            WHERE
                match_id = ?
                AND team_id = ?
            """,
            (
                match_id,
                team_id,
            ),
        ).fetchone()

        event_in = int(
            event_counts["in_count"] or 0
        )
        event_out = int(
            event_counts["out_count"] or 0
        )
        stats_in = int(
            stats_counts["in_count"] or 0
        )
        stats_out = int(
            stats_counts["out_count"] or 0
        )
        starters = int(
            stats_counts["starters"] or 0
        )

        status = (
            "OK"
            if (
                event_in == stats_in
                and event_out == stats_out
            )
            else "ABWEICHUNG"
        )

        print()
        print(
            f"[{status}] {team['team_name']}"
        )
        print(
            f"  Events: IN={event_in} "
            f"OUT={event_out}"
        )
        print(
            f"  Stats:  IN={stats_in} "
            f"OUT={stats_out} "
            f"Starter={starters}"
        )


def main() -> None:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Hauptdatenbank nicht gefunden: "
            f"{SOURCE_DB}"
        )

    if TEST_DB.exists():
        TEST_DB.unlink()

    shutil.copy2(
        SOURCE_DB,
        TEST_DB,
    )

    print("=" * 78)
    print("ALIAS-FIX EINZELSPIELTEST")
    print("=" * 78)
    print(
        f"Test-DB: {TEST_DB}"
    )
    print(
        "Haupt-DB wird NICHT verändert."
    )

    connection = sqlite3.connect(TEST_DB)
    connection.row_factory = sqlite3.Row

    browser = FussballDeBrowser()

    try:
        match = connection.execute(
            """
            SELECT
                match_id
            FROM matches
            WHERE external_id = ?
            LIMIT 1
            """,
            (MATCH_EXTERNAL_ID,),
        ).fetchone()

        if match is None:
            raise RuntimeError(
                "Gladbach - HSV ist in der "
                "Hauptdatenbank nicht vorhanden."
            )

        match_id = int(
            match["match_id"]
        )

        before_players, before_missing = (
            count_mapping_problems(
                connection,
                match_id,
            )
        )

        print()
        print("VOR REIMPORT")
        print("-" * 78)
        print(
            "Wechsel-Spieler gesamt: "
            f"{before_players}"
        )
        print(
            "Davon nicht im Lineup:   "
            f"{before_missing}"
        )

        browser.start(
            headless=False,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht "
                "erstellt werden."
            )

        importer = MatchDetailImporter(
            connection
        )

        result = importer.import_from_page(
            page=browser.page,
            source_url=MATCH_URL,
        )

        connection.commit()

        print()
        print("IMPORTERGEBNIS")
        print("-" * 78)
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

        after_players, after_missing = (
            count_mapping_problems(
                connection,
                match_id,
            )
        )

        print()
        print("NACH REIMPORT")
        print("-" * 78)
        print(
            "Wechsel-Spieler gesamt: "
            f"{after_players}"
        )
        print(
            "Davon nicht im Lineup:   "
            f"{after_missing}"
        )

        print_team_quality(
            connection,
            match_id,
        )

        print()
        print("=" * 78)

        if after_missing < before_missing:
            print(
                "ERGEBNIS: ALIAS-FIX GREIFT."
            )
        else:
            print(
                "ERGEBNIS: KEINE VERBESSERUNG "
                "BEI DER LINEUP-ZUORDNUNG."
            )

        if after_missing == 0:
            print(
                "Alle Wechsel-Spieler sind jetzt "
                "im Lineup verankert."
            )
        else:
            print(
                f"Noch {after_missing} Wechsel-Spieler "
                "fehlen im Lineup."
            )

        print("=" * 78)

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()
