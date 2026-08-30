from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.database.repositories.player_repository import PlayerRepository


SOURCE_DB = Path("data/database/alias_fix_test.db")
TEST_DB = Path("data/database/player_merge_test.db")

SOURCE_PLAYER_ID = 832
TARGET_PLAYER_ID = 1075


def row_dict(row):
    return dict(row) if row is not None else None


def find_references(connection, player_id):
    references = []

    tables = connection.execute(
        '''
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        '''
    ).fetchall()

    for (table_name,) in tables:
        columns = {
            row[1]
            for row in connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
        }

        for column_name in ("player_id", "related_player_id"):
            if column_name not in columns:
                continue

            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}" '
                f'WHERE "{column_name}" = ?',
                (player_id,),
            ).fetchone()[0]

            if count:
                references.append(
                    (table_name, column_name, int(count))
                )

    return references


def print_references(title, references):
    print()
    print(title)
    print("-" * 90)

    if not references:
        print("Keine Referenzen.")
        return

    for table_name, column_name, count in references:
        print(
            f"{table_name:<28} "
            f"{column_name:<20} "
            f"{count:>5}"
        )


def main():
    print("=" * 90)
    print("PLAYER-MERGE TEST 832 -> 1075")
    print("=" * 90)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Testquelle fehlt: {SOURCE_DB}"
        )

    shutil.copy2(SOURCE_DB, TEST_DB)

    print(f"Quelle:  {SOURCE_DB}")
    print(f"Test-DB: {TEST_DB}")
    print("Haupt-DB wird NICHT verändert.")

    connection = sqlite3.connect(TEST_DB)
    connection.row_factory = sqlite3.Row

    try:
        repository = PlayerRepository(connection)

        source_before = connection.execute(
            '''
            SELECT player_id, first_name, last_name, team_id, external_id
            FROM players
            WHERE player_id = ?
            ''',
            (SOURCE_PLAYER_ID,),
        ).fetchone()

        target_before = connection.execute(
            '''
            SELECT player_id, first_name, last_name, team_id, external_id
            FROM players
            WHERE player_id = ?
            ''',
            (TARGET_PLAYER_ID,),
        ).fetchone()

        print()
        print("VOR MERGE")
        print("-" * 90)
        print("Quelle:", row_dict(source_before))
        print("Ziel:  ", row_dict(target_before))

        print_references(
            "REFERENZEN AUF QUELLSPIELER VORHER",
            find_references(connection, SOURCE_PLAYER_ID),
        )

        source_aliases = [
            row[0]
            for row in connection.execute(
                '''
                SELECT external_id
                FROM player_external_ids
                WHERE player_id = ?
                ORDER BY external_id
                ''',
                (SOURCE_PLAYER_ID,),
            ).fetchall()
        ]

        print()
        print("QUELL-ALIASE")
        print("-" * 90)
        for alias in source_aliases:
            print(alias)

        result_id = repository.merge_players(
            source_player_id=SOURCE_PLAYER_ID,
            target_player_id=TARGET_PLAYER_ID,
            commit=True,
        )

        print()
        print("MERGE")
        print("-" * 90)
        print(f"Rückgabe player_id: {result_id}")

        source_after = connection.execute(
            '''
            SELECT *
            FROM players
            WHERE player_id = ?
            ''',
            (SOURCE_PLAYER_ID,),
        ).fetchone()

        target_after = connection.execute(
            '''
            SELECT player_id, first_name, last_name, team_id, external_id
            FROM players
            WHERE player_id = ?
            ''',
            (TARGET_PLAYER_ID,),
        ).fetchone()

        print()
        print("NACH MERGE")
        print("-" * 90)
        print("Quelle:", row_dict(source_after))
        print("Ziel:  ", row_dict(target_after))

        remaining = find_references(
            connection,
            SOURCE_PLAYER_ID,
        )

        print_references(
            "VERBLEIBENDE REFERENZEN AUF 832",
            remaining,
        )

        target_aliases = {
            row[0]
            for row in connection.execute(
                '''
                SELECT external_id
                FROM player_external_ids
                WHERE player_id = ?
                ''',
                (TARGET_PLAYER_ID,),
            ).fetchall()
        }

        missing_aliases = [
            alias
            for alias in source_aliases
            if alias not in target_aliases
        ]

        print()
        print("ALIAS-CHECK")
        print("-" * 90)
        print(f"Ziel-Aliase gesamt: {len(target_aliases)}")
        print(
            f"Fehlende Quell-Aliase: "
            f"{len(missing_aliases)}"
        )

        for alias in missing_aliases:
            print(f"  FEHLT: {alias}")

        lineup_251 = connection.execute(
            '''
            SELECT
                l.player_id,
                p.first_name,
                p.last_name,
                l.team_id,
                l.is_starting
            FROM lineups l
            JOIN players p
                ON p.player_id = l.player_id
            WHERE
                l.match_id = 251
                AND l.player_id = ?
            ''',
            (TARGET_PLAYER_ID,),
        ).fetchall()

        print()
        print("SPIEL 251 LINEUP")
        print("-" * 90)

        for row in lineup_251:
            print(dict(row))

        ok = (
            source_after is None
            and not remaining
            and not missing_aliases
            and len(lineup_251) == 1
        )

        print()
        print("=" * 90)
        print(
            "ERGEBNIS: MERGE SAUBER."
            if ok
            else "ERGEBNIS: MERGE NOCH NICHT SAUBER."
        )
        print("=" * 90)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
