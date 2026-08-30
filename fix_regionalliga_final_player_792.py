from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


MAIN_DB = Path(
    "data/database/kreisligamanager.db"
)

FINAL_DB = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)

PLAYER_ID = 792


def main() -> None:
    print("=" * 100)
    print("REGIONALLIGA FINAL-DB / PLAYER 792 KORREKTUR")
    print("=" * 100)
    print(f"Haupt-DB: {MAIN_DB}")
    print(f"Final-DB: {FINAL_DB}")
    print()

    if not MAIN_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {MAIN_DB}"
        )

    if not FINAL_DB.exists():
        raise FileNotFoundError(
            f"Final-DB fehlt: {FINAL_DB}"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = FINAL_DB.with_name(
        f"{FINAL_DB.stem}_before_player792_fix_{timestamp}.db"
    )

    shutil.copy2(
        FINAL_DB,
        backup_path,
    )

    print(
        f"Sicherheitskopie Final-DB: "
        f"{backup_path}"
    )

    main_connection = sqlite3.connect(
        MAIN_DB
    )
    main_connection.row_factory = sqlite3.Row

    final_connection = sqlite3.connect(
        FINAL_DB
    )
    final_connection.row_factory = sqlite3.Row

    try:
        main_player = main_connection.execute(
            """
            SELECT *
            FROM players
            WHERE player_id = ?
            """,
            (PLAYER_ID,),
        ).fetchone()

        final_player_before = final_connection.execute(
            """
            SELECT *
            FROM players
            WHERE player_id = ?
            """,
            (PLAYER_ID,),
        ).fetchone()

        if main_player is None:
            raise RuntimeError(
                f"player_id {PLAYER_ID} fehlt in der Haupt-DB."
            )

        if final_player_before is None:
            raise RuntimeError(
                f"player_id {PLAYER_ID} fehlt in der Final-DB."
            )

        print()
        print("HAUPT-DB")
        print("-" * 100)
        print(dict(main_player))

        print()
        print("FINAL-DB VORHER")
        print("-" * 100)
        print(dict(final_player_before))

        final_connection.execute(
            """
            UPDATE players
            SET
                team_id = ?,
                first_name = ?,
                last_name = ?,
                birthdate = ?,
                position = ?,
                shirt_number = ?,
                foot = ?,
                height_cm = ?,
                weight_kg = ?,
                nationality = ?,
                is_active = ?,
                external_id = ?
            WHERE player_id = ?
            """,
            (
                main_player["team_id"],
                main_player["first_name"],
                main_player["last_name"],
                main_player["birthdate"],
                main_player["position"],
                main_player["shirt_number"],
                main_player["foot"],
                main_player["height_cm"],
                main_player["weight_kg"],
                main_player["nationality"],
                main_player["is_active"],
                main_player["external_id"],
                PLAYER_ID,
            ),
        )

        final_connection.commit()

        final_player_after = final_connection.execute(
            """
            SELECT *
            FROM players
            WHERE player_id = ?
            """,
            (PLAYER_ID,),
        ).fetchone()

        print()
        print("FINAL-DB NACHHER")
        print("-" * 100)
        print(dict(final_player_after))

        if dict(main_player) != dict(final_player_after):
            raise RuntimeError(
                "Korrektur fehlgeschlagen: "
                "Spielerzeile stimmt noch nicht mit Haupt-DB überein."
            )

        print()
        print("=" * 100)
        print("ERGEBNIS")
        print("=" * 100)
        print(
            "OK - player_id 792 wurde in der Final-DB "
            "exakt auf den Stand der Haupt-DB zurückgesetzt."
        )
        print(
            "Die Haupt-DB wurde NICHT verändert."
        )
        print(
            "Als Nächstes erneut ausführen:"
        )
        print(
            "python check_regionalliga_db_promotion.py"
        )
        print("=" * 100)

    except Exception:
        final_connection.rollback()
        raise

    finally:
        main_connection.close()
        final_connection.close()


if __name__ == "__main__":
    main()
