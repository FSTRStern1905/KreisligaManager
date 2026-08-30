from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.database.repositories.player_repository import PlayerRepository


SOURCE_DB = Path(
    "data/database/backups/"
    "kreisligamanager_before_match_251_20260830_090332.db"
)
TEST_DB = Path(
    "data/database/player_merge_stats_test.db"
)

SOURCE_PLAYER_ID = 832
TARGET_PLAYER_ID = 1075
TEAM_ID = 21

CHECK_MATCHES = (
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


def get_stat_row(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
):
    return connection.execute(
        """
        SELECT
            player_match_stat_id,
            match_id,
            team_id,
            player_id,
            is_starting,
            was_substituted_in,
            was_substituted_out,
            minute_in,
            minute_out,
            minutes_played,
            goals,
            assists,
            yellow_cards,
            red_cards
        FROM player_match_stats
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


def get_starter_count(
    connection: sqlite3.Connection,
    match_id: int,
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM player_match_stats
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


def main() -> None:
    print("=" * 100)
    print("PLAYER_MATCH_STATS MERGE-PRESERVATION TEST")
    print("=" * 100)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Backup nicht gefunden: {SOURCE_DB}"
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

    try:
        repository = PlayerRepository(
            connection
        )

        source = repository.get(
            SOURCE_PLAYER_ID
        )
        target = repository.get(
            TARGET_PLAYER_ID
        )

        print()
        print("VOR MERGE")
        print("-" * 100)
        print("Quelle:", source)
        print("Ziel:  ", target)

        if source is None or target is None:
            raise RuntimeError(
                "Quell- oder Zielspieler fehlt im Backup."
            )

        before = {}

        print()
        print("STATS VORHER")
        print("-" * 100)

        for match_id in CHECK_MATCHES:
            source_row = get_stat_row(
                connection,
                match_id,
                SOURCE_PLAYER_ID,
            )
            target_row = get_stat_row(
                connection,
                match_id,
                TARGET_PLAYER_ID,
            )

            before[match_id] = (
                dict(source_row)
                if source_row is not None
                else None,
                dict(target_row)
                if target_row is not None
                else None,
            )

            print(
                f"Spiel {match_id}: "
                f"832={before[match_id][0]} | "
                f"1075={before[match_id][1]}"
            )

        repository.merge_players(
            source_player_id=SOURCE_PLAYER_ID,
            target_player_id=TARGET_PLAYER_ID,
            commit=True,
        )

        print()
        print("NACH MERGE")
        print("-" * 100)

        problems = []

        for match_id in CHECK_MATCHES:
            merged_row = get_stat_row(
                connection,
                match_id,
                TARGET_PLAYER_ID,
            )

            starters = get_starter_count(
                connection,
                match_id,
            )

            print(
                f"Spiel {match_id}: "
                f"Stats={dict(merged_row) if merged_row else None} | "
                f"Gladbach Starter={starters}"
            )

            if merged_row is None:
                problems.append(
                    f"Spiel {match_id}: Ziel-Stats fehlen."
                )
                continue

            source_before, target_before = (
                before[match_id]
            )

            expected_starting = max(
                int((source_before or {}).get("is_starting", 0) or 0),
                int((target_before or {}).get("is_starting", 0) or 0),
            )

            expected_sub_out = max(
                int((source_before or {}).get("was_substituted_out", 0) or 0),
                int((target_before or {}).get("was_substituted_out", 0) or 0),
            )

            if int(merged_row["is_starting"] or 0) != expected_starting:
                problems.append(
                    f"Spiel {match_id}: is_starting falsch."
                )

            if int(merged_row["was_substituted_out"] or 0) != expected_sub_out:
                problems.append(
                    f"Spiel {match_id}: was_substituted_out falsch."
                )

            if starters != 11:
                problems.append(
                    f"Spiel {match_id}: {starters} Starter statt 11."
                )

        source_after = repository.get(
            SOURCE_PLAYER_ID
        )

        if source_after is not None:
            problems.append(
                "Quellspieler 832 existiert noch."
            )

        print()
        print("=" * 100)

        if problems:
            print("ERGEBNIS: STATS-MERGE NOCH FEHLERHAFT.")
            for problem in problems:
                print(" -", problem)
        else:
            print(
                "ERGEBNIS: PLAYER_MATCH_STATS BLEIBEN SAUBER ERHALTEN."
            )

        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
