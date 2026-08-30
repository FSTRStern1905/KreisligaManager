from __future__ import annotations

import shutil
import sqlite3
import traceback
from collections import Counter
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

WORK_DB = Path(
    "data/database/regionalliga_live_int_error_diagnosis.db"
)

FAILED_MATCH_IDS = (
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


def build_match_url(
    external_id: str,
) -> str:
    return (
        "https://www.fussball.de/spiel/"
        "-/spiel/"
        f"{external_id}"
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
            m.home_goals,
            m.away_goals
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


def traceback_signature(
    tb_text: str,
) -> str:
    lines = [
        line.strip()
        for line in tb_text.splitlines()
        if line.strip()
    ]

    file_lines = [
        line
        for line in lines
        if line.startswith("File ")
    ]

    if file_lines:
        return file_lines[-1]

    return "keine Python-Dateizeile gefunden"


def main() -> None:
    print("=" * 110)
    print(
        "REGIONALLIGA SÜDWEST 2025/26 "
        "- LIVE int('') SAMMELDIAGNOSE"
    )
    print("=" * 110)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Regionalliga-Test-DB fehlt: {SOURCE_DB}"
        )

    print(f"Quelle: {SOURCE_DB}")
    print(
        "Haupt-DB wird NICHT verändert."
    )
    print(
        "Die 17 ehemals fehlerhaften Spiele werden "
        "über den echten import_from_page()-Pfad getestet."
    )

    browser = FussballDeBrowser()
    results: list[dict] = []
    signatures: Counter[str] = Counter()

    try:
        browser.start(
            headless=True,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht erstellt werden."
            )

        for index, external_id in enumerate(
            FAILED_MATCH_IDS,
            start=1,
        ):
            print()
            print("=" * 110)
            print(
                f"[{index}/{len(FAILED_MATCH_IDS)}] "
                f"{external_id}"
            )
            print("=" * 110)

            shutil.copy2(
                SOURCE_DB,
                WORK_DB,
            )

            connection = sqlite3.connect(
                WORK_DB
            )
            connection.row_factory = sqlite3.Row

            try:
                match_info = get_match_info(
                    connection,
                    external_id,
                )

                print("MATCH")
                print("-" * 110)
                print(
                    match_info
                    if match_info
                    else "(nicht gefunden)"
                )

                importer = MatchDetailImporter(
                    connection
                )

                try:
                    result = importer.import_from_page(
                        page=browser.page,
                        source_url=build_match_url(
                            external_id
                        ),
                    )

                    connection.commit()

                    print()
                    print("[OK] Live-Import erfolgreich.")
                    print(result)

                    results.append(
                        {
                            "external_id": external_id,
                            "status": "OK",
                            "signature": "",
                        }
                    )

                except Exception as exc:
                    connection.rollback()

                    tb_text = traceback.format_exc()
                    signature = traceback_signature(
                        tb_text
                    )

                    signatures[
                        signature
                    ] += 1

                    status = (
                        f"{type(exc).__name__}: {exc}"
                    )

                    print()
                    print(
                        f"[FEHLER] {status}"
                    )
                    print()
                    print("TRACEBACK")
                    print("-" * 110)
                    print(
                        tb_text.rstrip()
                    )

                    results.append(
                        {
                            "external_id": external_id,
                            "status": status,
                            "signature": signature,
                        }
                    )

                browser.page.wait_for_timeout(
                    1200
                )

            finally:
                connection.close()

    finally:
        browser.close()

    print()
    print("=" * 110)
    print("GESAMTERGEBNIS")
    print("=" * 110)

    for result in results:
        print(
            f"{result['external_id']} | "
            f"{result['status']}"
        )

        if result["signature"]:
            print(
                f"  -> {result['signature']}"
            )

    print()
    print("TRACEBACK-SIGNATUREN")
    print("-" * 110)

    if not signatures:
        print("(keine Fehler)")
    else:
        for signature, count in (
            signatures.most_common()
        ):
            print(
                f"{count:>2}x | {signature}"
            )

    int_errors = [
        result
        for result in results
        if "invalid literal for int()"
        in result["status"]
    ]

    http_503_errors = [
        result
        for result in results
        if "HTTP 503"
        in result["status"]
    ]

    print()
    print(
        f"Live int('')-Fehler: "
        f"{len(int_errors)}"
        f"/{len(FAILED_MATCH_IDS)}"
    )
    print(
        f"HTTP-503-Fälle:       "
        f"{len(http_503_errors)}"
        f"/{len(FAILED_MATCH_IDS)}"
    )

    print()
    print(
        "Wenn int('') jetzt reproduziert wird, zeigt "
        "der Traceback exakt die Live-Komponente, "
        "die leere Werte in int() umwandelt."
    )
    print("=" * 110)


if __name__ == "__main__":
    main()
