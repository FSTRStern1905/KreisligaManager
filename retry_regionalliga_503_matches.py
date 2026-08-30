from __future__ import annotations

import shutil
import sqlite3
import time
from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.match_detail_importer import (
    MatchDetailImporter,
)


SOURCE_DB = Path(
    "data/database/regionalliga_suedwest_2526_import_test.db"
)

RETRY_DB = Path(
    "data/database/regionalliga_suedwest_2526_retry_test.db"
)

FAILED_503_IDS = (
    "02TNUVASR0000000VS5489BUVSSD35NB",
    "02TNUVASV0000000VS5489BUVSSD35NB",
    "02TNUVAT2S000000VS5489BUVSSD35NB",
    "02TNUVATHC000000VS5489BUVSSD35NB",
    "02TNUVATLK000000VS5489BUVSSD35NB",
    "02TNUVATQ0000000VS5489BUVSSD35NB",
    "02TNUVAU4O000000VS5489BUVSSD35NB",
    "02TNUVAUG0000000VS5489BUVSSD35NB",
    "02TNUVAVP0000000VS5489BUVSSD35NB",
    "02TNUVB0DG000000VS5489BUVSSD35NB",
    "02TNUVB0N0000000VS5489BUVSSD35NB",
    "02TNUVB0VG000000VS5489BUVSSD35NB",
    "02TNUVB150000000VS5489BUVSSD35NB",
    "02TNUVB1DK000000VS5489BUVSSD35NB",
    "02TNUVB1M8000000VS5489BUVSSD35NB",
    "02TNUVB288000000VS5489BUVSSD35NB",
    "02TNUVB2VO000000VS5489BUVSSD35NB",
    "02TNUVB32O000000VS5489BUVSSD35NB",
    "02TNUVB3HG000000VS5489BUVSSD35NB",
    "02TNUVB3QO000000VS5489BUVSSD35NB",
    "02TNUVB3TO000000VS5489BUVSSD35NB",
    "02TNUVB46S000000VS5489BUVSSD35NB",
    "02TNUVB4A0000000VS5489BUVSSD35NB",
    "02TNUVB4LC000000VS5489BUVSSD35NB",
    "02TNUVB51S000000VS5489BUVSSD35NB",
    "02TNUVB550000000VS5489BUVSSD35NB",
    "02TNUVB6BG000000VS5489BUVSSD35NB",
    "02TNUVBC58000000VS5489BUVSSD35NB",
)

MAX_ATTEMPTS = 5
BASE_WAIT_SECONDS = 4.0
BETWEEN_MATCHES_SECONDS = 1.5


def build_match_url(
    external_id: str,
) -> str:
    return (
        "https://www.fussball.de/spiel/"
        "-/spiel/"
        f"{external_id}"
    )


def prepare_retry_database() -> None:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Regionalliga-Test-DB fehlt: {SOURCE_DB}"
        )

    if RETRY_DB.exists():
        RETRY_DB.unlink()

    shutil.copy2(
        SOURCE_DB,
        RETRY_DB,
    )


def get_match_info(
    connection: sqlite3.Connection,
    external_id: str,
) -> dict:
    row = connection.execute(
        """
        SELECT
            m.match_id,
            m.matchday,
            m.external_id,
            ht.name AS home_team,
            at.name AS away_team,
            m.detail_imported
        FROM matches AS m
        LEFT JOIN teams AS ht
            ON ht.team_id = m.home_team_id
        LEFT JOIN teams AS at
            ON at.team_id = m.away_team_id
        WHERE m.external_id = ?
        """,
        (external_id,),
    ).fetchone()

    return dict(row) if row else {}


def start_browser() -> FussballDeBrowser:
    browser = FussballDeBrowser()
    browser.start(
        headless=True,
    )

    if browser.page is None:
        browser.close()
        raise RuntimeError(
            "Browserseite konnte nicht erstellt werden."
        )

    return browser


def print_quality(
    connection: sqlite3.Connection,
) -> None:
    competition = connection.execute(
        """
        SELECT competition_id
        FROM competitions
        WHERE name = 'Regionalliga Südwest'
        ORDER BY competition_id DESC
        LIMIT 1
        """
    ).fetchone()

    if competition is None:
        print(
            "Regionalliga-Wettbewerb nicht gefunden."
        )
        return

    competition_id = int(
        competition["competition_id"]
    )

    matches = connection.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE
                    WHEN detail_imported = 1
                    THEN 1
                    ELSE 0
                END
            ) AS detail_imported
        FROM matches
        WHERE competition_id = ?
        """,
        (competition_id,),
    ).fetchone()

    lineups = connection.execute(
        """
        SELECT
            COUNT(DISTINCT l.match_id) AS cnt
        FROM lineups AS l
        INNER JOIN matches AS m
            ON m.match_id = l.match_id
        WHERE m.competition_id = ?
        """,
        (competition_id,),
    ).fetchone()

    events = connection.execute(
        """
        SELECT
            COUNT(DISTINCT e.match_id) AS cnt
        FROM events AS e
        INNER JOIN matches AS m
            ON m.match_id = e.match_id
        WHERE m.competition_id = ?
        """,
        (competition_id,),
    ).fetchone()

    stats = connection.execute(
        """
        SELECT
            COUNT(DISTINCT pms.match_id) AS cnt
        FROM player_match_stats AS pms
        INNER JOIN matches AS m
            ON m.match_id = pms.match_id
        WHERE m.competition_id = ?
        """,
        (competition_id,),
    ).fetchone()

    spectators = connection.execute(
        """
        SELECT
            COUNT(*) AS cnt
        FROM matches
        WHERE
            competition_id = ?
            AND attendance IS NOT NULL
        """,
        (competition_id,),
    ).fetchone()

    print()
    print("=" * 100)
    print("QUALITÄT NACH 503-RETRY")
    print("=" * 100)
    print(
        f"Spiele gesamt:           "
        f"{int(matches['total'] or 0)}"
    )
    print(
        f"Detailimportiert:         "
        f"{int(matches['detail_imported'] or 0)}"
    )
    print(
        f"Spiele mit Lineup:       "
        f"{int(lineups['cnt'] or 0)}"
    )
    print(
        f"Spiele mit Events:       "
        f"{int(events['cnt'] or 0)}"
    )
    print(
        f"Spiele mit Player-Stats: "
        f"{int(stats['cnt'] or 0)}"
    )
    print(
        f"Spiele mit Zuschauern:   "
        f"{int(spectators['cnt'] or 0)}"
    )
    print("=" * 100)


def main() -> None:
    print("=" * 100)
    print(
        "REGIONALLIGA SÜDWEST 2025/26 "
        "- HTTP-503 RETRY"
    )
    print("=" * 100)

    prepare_retry_database()

    print(f"Quelle:   {SOURCE_DB}")
    print(f"Retry-DB: {RETRY_DB}")
    print(
        "Haupt-DB wird NICHT verändert."
    )
    print(
        f"503-Fälle: {len(FAILED_503_IDS)}"
    )

    connection = sqlite3.connect(
        RETRY_DB
    )
    connection.row_factory = sqlite3.Row

    successful: list[str] = []
    failed: list[tuple[str, str]] = []

    browser: FussballDeBrowser | None = None

    try:
        browser = start_browser()

        for index, external_id in enumerate(
            FAILED_503_IDS,
            start=1,
        ):
            print()
            print("=" * 100)
            print(
                f"[{index}/{len(FAILED_503_IDS)}] "
                f"{external_id}"
            )
            print("=" * 100)

            info = get_match_info(
                connection,
                external_id,
            )

            print(
                info
                if info
                else "(Spiel nicht gefunden)"
            )

            success = False
            last_error = ""

            for attempt in range(
                1,
                MAX_ATTEMPTS + 1,
            ):
                print(
                    f"Versuch {attempt}/"
                    f"{MAX_ATTEMPTS} ..."
                )

                try:
                    importer = MatchDetailImporter(
                        connection
                    )

                    result = importer.import_from_page(
                        page=browser.page,
                        source_url=build_match_url(
                            external_id
                        ),
                    )

                    connection.commit()

                    print("[OK]")
                    print(result)

                    successful.append(
                        external_id
                    )

                    success = True
                    break

                except Exception as exc:
                    connection.rollback()

                    last_error = (
                        f"{type(exc).__name__}: {exc}"
                    )

                    print(
                        f"[FEHLER] {last_error}"
                    )

                    if browser is not None:
                        browser.close()

                    wait_seconds = (
                        BASE_WAIT_SECONDS
                        * attempt
                    )

                    print(
                        f"Warte {wait_seconds:.1f}s "
                        "und starte Browser neu ..."
                    )

                    time.sleep(
                        wait_seconds
                    )

                    browser = start_browser()

            if not success:
                failed.append(
                    (
                        external_id,
                        last_error,
                    )
                )

            time.sleep(
                BETWEEN_MATCHES_SECONDS
            )

        print()
        print("=" * 100)
        print("RETRY-ERGEBNIS")
        print("=" * 100)
        print(
            f"Erfolgreich: "
            f"{len(successful)}/"
            f"{len(FAILED_503_IDS)}"
        )
        print(
            f"Fehlgeschlagen: "
            f"{len(failed)}"
        )

        if failed:
            print()
            print("VERBLEIBENDE FEHLER")
            print("-" * 100)

            for external_id, error in failed:
                print(
                    f"{external_id} | {error}"
                )

        print_quality(
            connection
        )

    finally:
        if browser is not None:
            browser.close()

        connection.close()


if __name__ == "__main__":
    main()
