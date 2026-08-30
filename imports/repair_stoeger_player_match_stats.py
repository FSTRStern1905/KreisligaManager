from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")
BACKUP_DIR = Path("data/database/backups")

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


def starter_count(
    connection: sqlite3.Connection,
    match_id: int,
) -> int:
    return int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM player_match_stats
            WHERE match_id = ?
              AND team_id = ?
              AND is_starting = 1
            """,
            (match_id, TEAM_ID),
        ).fetchone()[0]
        or 0
    )


def main() -> None:
    print("=" * 90)
    print("REPARATUR: KEVIN STÖGER PLAYER_MATCH_STATS")
    print("=" * 90)

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / (
        f"kreisligamanager_before_stoeger_stats_fix_{timestamp}.db"
    )
    shutil.copy2(DB_PATH, backup)

    print(f"Haupt-DB: {DB_PATH}")
    print(f"Backup:   {backup}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("BEGIN IMMEDIATE")

        for match_id in MATCH_IDS:
            lineup = connection.execute(
                """
                SELECT is_starting
                FROM lineups
                WHERE match_id = ?
                  AND team_id = ?
                  AND player_id = ?
                """,
                (match_id, TEAM_ID, PLAYER_ID),
            ).fetchone()

            stats = connection.execute(
                """
                SELECT player_match_stat_id, is_starting
                FROM player_match_stats
                WHERE match_id = ?
                  AND team_id = ?
                  AND player_id = ?
                """,
                (match_id, TEAM_ID, PLAYER_ID),
            ).fetchone()

            if lineup is None or int(lineup["is_starting"] or 0) != 1:
                raise RuntimeError(
                    f"Spiel {match_id}: Lineup-Starterflag ist nicht sauber."
                )

            if stats is None:
                raise RuntimeError(
                    f"Spiel {match_id}: player_match_stats fehlt."
                )

            connection.execute(
                """
                UPDATE player_match_stats
                SET
                    is_starting = 1,
                    minute_in = CASE
                        WHEN minute_in IS NULL THEN 0
                        ELSE minute_in
                    END
                WHERE match_id = ?
                  AND team_id = ?
                  AND player_id = ?
                """,
                (match_id, TEAM_ID, PLAYER_ID),
            )

        problems = []

        print()
        print("ABSCHLUSSPRÜFUNG")
        print("-" * 90)

        for match_id in MATCH_IDS:
            row = connection.execute(
                """
                SELECT
                    match_id,
                    player_id,
                    is_starting,
                    was_substituted_in,
                    was_substituted_out,
                    minute_in,
                    minute_out,
                    minutes_played
                FROM player_match_stats
                WHERE match_id = ?
                  AND team_id = ?
                  AND player_id = ?
                """,
                (match_id, TEAM_ID, PLAYER_ID),
            ).fetchone()

            starters = starter_count(connection, match_id)

            print(
                f"Spiel {match_id}: "
                f"Stats={dict(row) if row else None} | "
                f"Starter={starters}"
            )

            if row is None:
                problems.append(f"Spiel {match_id}: Stats fehlen.")
                continue

            if int(row["is_starting"] or 0) != 1:
                problems.append(
                    f"Spiel {match_id}: is_starting != 1."
                )

            if starters != 11:
                problems.append(
                    f"Spiel {match_id}: {starters} Starter statt 11."
                )

        if problems:
            connection.rollback()
            print()
            print("ERGEBNIS: REPARATUR FEHLGESCHLAGEN – ROLLBACK.")
            for problem in problems:
                print(" -", problem)
            raise RuntimeError("Qualitätsprüfung fehlgeschlagen.")

        connection.commit()

        print()
        print("=" * 90)
        print("ERGEBNIS: PLAYER_MATCH_STATS REPARATUR ERFOLGREICH.")
        print("Alle 10 Gladbach-Spiele haben wieder 11 Starter.")
        print("=" * 90)

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
