from __future__ import annotations

import shutil
import sqlite3
import traceback
from collections import Counter
from pathlib import Path

from src.importer.fussballde.match_detail_importer import (
    MatchDetailImporter,
)


SOURCE_DB = Path(
    "data/database/regionalliga_suedwest_2526_import_test.db"
)

WORK_DB = Path(
    "data/database/regionalliga_int_error_diagnosis.db"
)

DEBUG_HTML_DIR = Path(
    "debug/html/matches"
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


def build_source_url(
    match_external_id: str,
) -> str:
    return (
        "https://www.fussball.de/spiel/"
        "-/spiel/"
        f"{match_external_id}"
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

    if row is None:
        return {}

    return dict(row)


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
        "- int('') SAMMELDIAGNOSE"
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
        "Jeder Fall läuft auf einer frischen Kopie "
        "der Regionalliga-Test-DB."
    )

    results: list[dict] = []
    signatures: Counter[str] = Counter()

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

        html_path = (
            DEBUG_HTML_DIR
            / f"{external_id}.html"
        )

        if not html_path.exists():
            print(
                f"[FEHLT] Debug-HTML nicht gefunden: "
                f"{html_path}"
            )

            results.append(
                {
                    "external_id": external_id,
                    "status": "HTML_FEHLT",
                    "signature": "",
                }
            )
            continue

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

            html = html_path.read_text(
                encoding="utf-8",
                errors="replace",
            )

            print(
                f"Debug-HTML: {html_path} "
                f"({len(html)} Zeichen)"
            )

            importer = MatchDetailImporter(
                connection
            )

            try:
                result = importer.import_from_html(
                    html=html,
                    source_url=build_source_url(
                        external_id
                    ),
                    page=None,
                )

                print()
                print("[OK] Fehler nicht reproduziert.")
                print(result)

                results.append(
                    {
                        "external_id": external_id,
                        "status": "OK",
                        "signature": "",
                    }
                )

            except Exception as exc:
                tb_text = traceback.format_exc()
                signature = traceback_signature(
                    tb_text
                )

                signatures[
                    signature
                ] += 1

                print()
                print(
                    f"[FEHLER] "
                    f"{type(exc).__name__}: {exc}"
                )
                print()
                print("TRACEBACK")
                print("-" * 110)
                print(tb_text.rstrip())

                results.append(
                    {
                        "external_id": external_id,
                        "status": (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                        "signature": signature,
                    }
                )

        finally:
            connection.close()

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
        print("(keine reproduzierten Python-Fehler)")
    else:
        for signature, count in (
            signatures.most_common()
        ):
            print(
                f"{count:>2}x | {signature}"
            )

    int_empty_errors = [
        result
        for result in results
        if "invalid literal for int()"
        in result["status"]
    ]

    print()
    print(
        "Reproduzierte int('')-Fehler: "
        f"{len(int_empty_errors)}"
        f"/{len(FAILED_MATCH_IDS)}"
    )

    print()
    print(
        "Wenn mehrere Fälle auf dieselbe letzte "
        "Python-Dateizeile zeigen, haben wir den "
        "zentralen Parser-/Importer-Bug lokalisiert."
    )
    print("=" * 110)


if __name__ == "__main__":
    main()
