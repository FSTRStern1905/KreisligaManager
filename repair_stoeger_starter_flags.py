from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

BACKUP_DIR = Path(
    "data/database/backups"
)

PLAYER_ID = 1075
TEAM_ID = 21

MATCH_IDS = (
    195,
    210,
    222,
    366,
    373,
    425,
    449,
    467,
    476,
    485,
)


def get_starter_count(
    connection: sqlite3.Connection,
    match_id: int,
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM lineups
        WHERE
            match_id = ?
            AND team_id = ?
            AND is_starting = 1
        """,
        (
            match_id,
            TEAM_ID,
        ),
    ).fetchone()

    return int(row[0] or 0)


def get_player_lineup(
    connection: sqlite3.Connection,
    match_id: int,
):
    return connection.execute(
        """
        SELECT
            match_id,
            team_id,
            player_id,
            is_starting,
            shirt_number,
            position
        FROM lineups
        WHERE
            match_id = ?
            AND team_id = ?
            AND player_id = ?
        LIMIT 1
        """,
        (
            match_id,
            TEAM_ID,
            PLAYER_ID,
        ),
    ).fetchone()


def main() -> None:
    print("=" * 90)
    print("REPARATUR: KEVIN STÖGER STARTERFLAGS")
    print("=" * 90)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Hauptdatenbank nicht gefunden: {DB_PATH}"
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = BACKUP_DIR / (
        "kreisligamanager_before_stoeger_"
        f"starter_fix_{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    print(f"Haupt-DB: {DB_PATH}")
    print(f"Backup:   {backup_path}")
    print()

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        player = connection.execute(
            """
            SELECT
                player_id,
                first_name,
                last_name,
                team_id
            FROM players
            WHERE player_id = ?
            LIMIT 1
            """,
            (PLAYER_ID,),
        ).fetchone()

        if player is None:
            raise RuntimeError(
                "Kevin Stöger (player_id=1075) "
                "wurde nicht gefunden."
            )

        print(
            "Spieler:",
            dict(player),
        )

        print()
        print("VOR REPARATUR")
        print("-" * 90)

        for match_id in MATCH_IDS:
            row = get_player_lineup(
                connection,
                match_id,
            )

            starters = get_starter_count(
                connection,
                match_id,
            )

            print(
                f"Spiel {match_id}: "
                f"Lineup={dict(row) if row else None} | "
                f"Starter={starters}"
            )

            if row is None:
                raise RuntimeError(
                    f"Spiel {match_id}: "
                    "Kevin Stöger fehlt im Lineup."
                )

        connection.execute(
            "BEGIN IMMEDIATE"
        )

        for match_id in MATCH_IDS:
            connection.execute(
                """
                UPDATE lineups
                SET is_starting = 1
                WHERE
                    match_id = ?
                    AND team_id = ?
                    AND player_id = ?
                """,
                (
                    match_id,
                    TEAM_ID,
                    PLAYER_ID,
                ),
            )

        print()
        print("NACH REPARATUR")
        print("-" * 90)

        problems = []

        for match_id in MATCH_IDS:
            row = get_player_lineup(
                connection,
                match_id,
            )

            starters = get_starter_count(
                connection,
                match_id,
            )

            print(
                f"Spiel {match_id}: "
                f"Lineup={dict(row) if row else None} | "
                f"Starter={starters}"
            )

            if row is None:
                problems.append(
                    f"Spiel {match_id}: "
                    "Kevin Stöger fehlt."
                )
                continue

            if int(
                row["is_starting"] or 0
            ) != 1:
                problems.append(
                    f"Spiel {match_id}: "
                    "Starterflag ist nicht 1."
                )

            if starters != 11:
                problems.append(
                    f"Spiel {match_id}: "
                    f"{starters} Starter statt 11."
                )

        print()
        print("=" * 90)

        if problems:
            connection.rollback()

            print(
                "ERGEBNIS: REPARATUR FEHLGESCHLAGEN."
            )
            print(
                "Änderungen wurden zurückgerollt."
            )

            for problem in problems:
                print(" -", problem)

            raise RuntimeError(
                "Starter-Reparatur hat die "
                "Qualitätsprüfung nicht bestanden."
            )

        connection.commit()

        print(
            "ERGEBNIS: REPARATUR ERFOLGREICH."
        )
        print(
            "Alle 10 Gladbach-Spiele haben "
            "wieder 11 Starter."
        )
        print("=" * 90)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
