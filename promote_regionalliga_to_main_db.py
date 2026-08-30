from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


MAIN_DB = Path("data/database/kreisligamanager.db")
FINAL_DB = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)
BACKUP_DIR = Path("data/database/backups")
REGIONALLIGA_NAME = "Regionalliga Südwest"


def integrity_check(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if result is None or result[0] != "ok":
            raise RuntimeError(
                f"Integrity-Check fehlgeschlagen für {path}: {result}"
            )
    finally:
        connection.close()


def has_regionalliga(path: Path) -> bool:
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            """
            SELECT competition_id
            FROM competitions
            WHERE name = ?
            LIMIT 1
            """,
            (REGIONALLIGA_NAME,),
        ).fetchone()

        return row is not None
    finally:
        connection.close()


def main() -> None:
    print("=" * 100)
    print("REGIONALLIGA FINAL-DB -> HAUPT-DB PROMOTION")
    print("=" * 100)
    print(f"Haupt-DB: {MAIN_DB}")
    print(f"Final-DB: {FINAL_DB}")

    if not MAIN_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {MAIN_DB}"
        )

    if not FINAL_DB.exists():
        raise FileNotFoundError(
            f"Final-DB fehlt: {FINAL_DB}"
        )

    print()
    print("[1/5] Integrity-Check Final-DB ...")
    integrity_check(FINAL_DB)
    print("OK")

    if not has_regionalliga(FINAL_DB):
        raise RuntimeError(
            "Regionalliga Südwest fehlt in der Final-DB."
        )

    print()
    print("[2/5] Backup der aktuellen Haupt-DB ...")
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    backup_path = BACKUP_DIR / (
        f"kreisligamanager_before_regionalliga_{timestamp}.db"
    )

    shutil.copy2(
        MAIN_DB,
        backup_path,
    )
    integrity_check(backup_path)
    print(f"OK: {backup_path}")

    print()
    print("[3/5] Final-DB wird als neue Haupt-DB kopiert ...")

    temp_path = MAIN_DB.with_name(
        "kreisligamanager_promotion_tmp.db"
    )

    if temp_path.exists():
        temp_path.unlink()

    shutil.copy2(
        FINAL_DB,
        temp_path,
    )

    integrity_check(temp_path)

    print()
    print("[4/5] Haupt-DB wird ersetzt ...")
    temp_path.replace(MAIN_DB)
    print("OK")

    print()
    print("[5/5] Abschlussprüfung ...")
    integrity_check(MAIN_DB)

    if not has_regionalliga(MAIN_DB):
        raise RuntimeError(
            "Promotion fehlgeschlagen: "
            "Regionalliga Südwest fehlt in der neuen Haupt-DB."
        )

    connection = sqlite3.connect(MAIN_DB)
    connection.row_factory = sqlite3.Row

    try:
        competition = connection.execute(
            """
            SELECT
                competition_id,
                name,
                season_id,
                league_id
            FROM competitions
            WHERE name = ?
            LIMIT 1
            """,
            (REGIONALLIGA_NAME,),
        ).fetchone()

        match_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM matches
            WHERE competition_id = ?
            """,
            (competition["competition_id"],),
        ).fetchone()[0]

        print("OK")
        print()
        print("=" * 100)
        print("PROMOTION ERFOLGREICH")
        print("=" * 100)
        print(dict(competition))
        print(f"Regionalliga-Spiele: {match_count}")
        print(f"Backup alte Haupt-DB: {backup_path}")
        print()
        print(
            "data/database/kreisligamanager.db "
            "enthält jetzt die geprüften Regionalliga-Daten."
        )
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
