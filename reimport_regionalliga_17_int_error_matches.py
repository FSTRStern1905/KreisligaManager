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
    "data/database/regionalliga_suedwest_2526_retry_test.db"
)

FINAL_DB = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)

MATCH_IDS = (
    "02TNUVB3KG000000VS5489BUVSSD35NB",
    "02TNUVB6ES000000VS5489BUVSSD35NB",
    "02TNUVB7TK000000VS5489BUVSSD35NB",
    "02TNUVB84C000000VS5489BUVSSD35NB",
    "02TNUVB8S8000000VS5489BUVSSD35NB",
    "02TNUVBA3C000000VS5489BUVSSD35NB",
    "02TNUVBD3K000000VS5489BUVSSD35NB",
    "02TNUVBDMS000000VS5489BUVSSD35NB",
    "02TNUVBIRC000000VS5489BUVSSD35NB",
    "02TNUVBJ44000000VS5489BUVSSD35NB",
    "02TNUVBK7G000000VS5489BUVSSD35NB",
    "02TNUVBL2O000000VS5489BUVSSD35NB",
    "02TNUVBMSS000000VS5489BUVSSD35NB",
    "02TNUVBQL4000000VS5489BUVSSD35NB",
    "02TNUVBRHS000000VS5489BUVSSD35NB",
    "02TNUVBRRG000000VS5489BUVSSD35NB",
    "02TNUVBTHK000000VS5489BUVSSD35NB",
)

MAX_ATTEMPTS = 3
WAIT_SECONDS = 2.0


def build_url(
    external_id: str,
) -> str:
    return (
        "https://www.fussball.de/spiel/"
        "-/spiel/"
        f"{external_id}"
    )


def prepare_database() -> None:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Quell-DB fehlt: {SOURCE_DB}"
        )

    if FINAL_DB.exists():
        FINAL_DB.unlink()

    shutil.copy2(
        SOURCE_DB,
        FINAL_DB,
    )


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


def get_match(
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
            at.name AS away_team
        FROM matches AS m
        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id
        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id
        WHERE m.external_id = ?
        """,
        (external_id,),
    ).fetchone()

    return dict(row) if row else {}


def get_counts(
    connection: sqlite3.Connection,
    match_id: int,
) -> dict:
    lineups = connection.execute(
        """
        SELECT COUNT(*)
        FROM lineups
        WHERE match_id = ?
        """,
        (match_id,),
    ).fetchone()[0]

    events = connection.execute(
        """
        SELECT COUNT(*)
        FROM events
        WHERE match_id = ?
        """,
        (match_id,),
    ).fetchone()[0]

    stats = connection.execute(
        """
        SELECT COUNT(*)
        FROM player_match_stats
        WHERE match_id = ?
        """,
        (match_id,),
    ).fetchone()[0]

    return {
        "lineups": int(lineups or 0),
        "events": int(events or 0),
        "stats": int(stats or 0),
    }


def main() -> None:
    print("=" * 110)
    print(
        "REGIONALLIGA SÜDWEST 2025/26 "
        "- REIMPORT DER 17 int('')-SPIELE"
    )
    print("=" * 110)

    prepare_database()

    print(f"Quelle:  {SOURCE_DB}")
    print(f"Final-DB:{FINAL_DB}")
    print(
        "Haupt-DB wird NICHT verändert."
    )

    connection = sqlite3.connect(
        FINAL_DB
    )
    connection.row_factory = sqlite3.Row

    browser: FussballDeBrowser | None = None
    successful: list[str] = []
    failed: list[tuple[str, str]] = []

    try:
        browser = start_browser()

        for index, external_id in enumerate(
            MATCH_IDS,
            start=1,
        ):
            print()
            print("=" * 110)
            print(
                f"[{index}/{len(MATCH_IDS)}] "
                f"{external_id}"
            )
            print("=" * 110)

            match = get_match(
                connection,
                external_id,
            )

            if not match:
                print("[FEHLER] Spiel nicht gefunden.")
                failed.append(
                    (
                        external_id,
                        "Spiel nicht gefunden",
                    )
                )
                continue

            match_id = int(
                match["match_id"]
            )

            print(match)

            before = get_counts(
                connection,
                match_id,
            )

            print(
                f"Vorher: "
                f"Lineups={before['lineups']} | "
                f"Events={before['events']} | "
                f"Stats={before['stats']}"
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
                        source_url=build_url(
                            external_id
                        ),
                    )

                    connection.commit()

                    after = get_counts(
                        connection,
                        match_id,
                    )

                    print("[OK]")
                    print(result)
                    print(
                        f"Nachher: "
                        f"Lineups={after['lineups']} | "
                        f"Events={after['events']} | "
                        f"Stats={after['stats']}"
                    )

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

                    time.sleep(
                        WAIT_SECONDS
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
                1.0
            )

        print()
        print("=" * 110)
        print("GESAMTERGEBNIS")
        print("=" * 110)
        print(
            f"Erfolgreich: "
            f"{len(successful)}/"
            f"{len(MATCH_IDS)}"
        )
        print(
            f"Fehlgeschlagen: "
            f"{len(failed)}"
        )

        if failed:
            print()
            for external_id, error in failed:
                print(
                    f"{external_id} | {error}"
                )

        missing_stats = connection.execute(
            """
            SELECT COUNT(*)
            FROM matches AS m
            WHERE
                m.competition_id = (
                    SELECT competition_id
                    FROM competitions
                    WHERE name = 'Regionalliga Südwest'
                    ORDER BY competition_id DESC
                    LIMIT 1
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM player_match_stats AS pms
                    WHERE pms.match_id = m.match_id
                )
            """
        ).fetchone()[0]

        matches_with_events = connection.execute(
            """
            SELECT COUNT(DISTINCT e.match_id)
            FROM events AS e
            INNER JOIN matches AS m
                ON m.match_id = e.match_id
            WHERE
                m.competition_id = (
                    SELECT competition_id
                    FROM competitions
                    WHERE name = 'Regionalliga Südwest'
                    ORDER BY competition_id DESC
                    LIMIT 1
                )
            """
        ).fetchone()[0]

        print()
        print(
            f"Spiele ohne Player-Stats danach: "
            f"{int(missing_stats or 0)}"
        )
        print(
            f"Spiele mit Events danach: "
            f"{int(matches_with_events or 0)}/306"
        )
        print(
            f"Finale Test-DB: {FINAL_DB}"
        )
        print("=" * 110)

    finally:
        if browser is not None:
            browser.close()

        connection.close()


if __name__ == "__main__":
    main()
