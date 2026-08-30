from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)


SOURCE_DB = Path(
    "data/database/player_match_stats_builder_interval_test.db"
)

TEST_DB = Path(
    "data/database/match_162_player_merge_test_v2.db"
)

MATCH_ID = 162

SOURCE_PLAYER_ID = 584
TARGET_PLAYER_ID = 436


def row_dict(
    row: sqlite3.Row | None,
) -> dict | None:
    if row is None:
        return None

    return dict(row)


def get_player(
    connection: sqlite3.Connection,
    player_id: int,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            player_id,
            team_id,
            first_name,
            last_name,
            external_id
        FROM players
        WHERE player_id = ?
        """,
        (player_id,),
    ).fetchone()


def get_aliases(
    connection: sqlite3.Connection,
    player_id: int,
) -> list[str]:
    return [
        str(row["external_id"])
        for row in connection.execute(
            """
            SELECT external_id
            FROM player_external_ids
            WHERE player_id = ?
            ORDER BY external_id
            """,
            (player_id,),
        ).fetchall()
    ]


def get_lineup_team_ids(
    connection: sqlite3.Connection,
    player_id: int,
) -> list[int]:
    return [
        int(row["team_id"])
        for row in connection.execute(
            """
            SELECT DISTINCT team_id
            FROM lineups
            WHERE
                match_id = ?
                AND player_id = ?
            ORDER BY team_id
            """,
            (
                MATCH_ID,
                player_id,
            ),
        ).fetchall()
    ]


def get_event_team_ids(
    connection: sqlite3.Connection,
    player_id: int,
) -> list[int]:
    rows = connection.execute(
        """
        SELECT DISTINCT team_id
        FROM events
        WHERE
            match_id = ?
            AND (
                player_id = ?
                OR related_player_id = ?
            )
            AND team_id IS NOT NULL
        ORDER BY team_id
        """,
        (
            MATCH_ID,
            player_id,
            player_id,
        ),
    ).fetchall()

    return [
        int(row["team_id"])
        for row in rows
    ]


def get_match_refs(
    connection: sqlite3.Connection,
    player_id: int,
) -> dict:
    result: dict[str, list[dict]] = {}

    result["lineups"] = [
        dict(row)
        for row in connection.execute(
            """
            SELECT
                lineup_id,
                match_id,
                team_id,
                player_id,
                is_starting
            FROM lineups
            WHERE
                match_id = ?
                AND player_id = ?
            ORDER BY lineup_id
            """,
            (
                MATCH_ID,
                player_id,
            ),
        ).fetchall()
    ]

    result["events_player_id"] = [
        dict(row)
        for row in connection.execute(
            """
            SELECT
                e.event_id,
                et.code,
                e.minute,
                e.team_id,
                e.player_id,
                e.related_player_id
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            WHERE
                e.match_id = ?
                AND e.player_id = ?
            ORDER BY
                e.minute,
                e.event_id
            """,
            (
                MATCH_ID,
                player_id,
            ),
        ).fetchall()
    ]

    result["events_related_player_id"] = [
        dict(row)
        for row in connection.execute(
            """
            SELECT
                e.event_id,
                et.code,
                e.minute,
                e.team_id,
                e.player_id,
                e.related_player_id
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            WHERE
                e.match_id = ?
                AND e.related_player_id = ?
            ORDER BY
                e.minute,
                e.event_id
            """,
            (
                MATCH_ID,
                player_id,
            ),
        ).fetchall()
    ]

    result["player_match_stats"] = [
        dict(row)
        for row in connection.execute(
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
                minutes_played
            FROM player_match_stats
            WHERE
                match_id = ?
                AND player_id = ?
            ORDER BY player_match_stat_id
            """,
            (
                MATCH_ID,
                player_id,
            ),
        ).fetchall()
    ]

    return result


def print_refs(
    title: str,
    refs: dict,
) -> None:
    print()
    print(title)
    print("-" * 110)

    for table_name, rows in refs.items():
        print(f"{table_name}:")

        if not rows:
            print("  (keine)")
            continue

        for row in rows:
            print(f"  {row}")


def get_team_minutes(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.team_id,
            t.name AS team_name,
            COUNT(*) AS squad_size,
            SUM(
                CASE
                    WHEN pms.is_starting = 1
                    THEN 1
                    ELSE 0
                END
            ) AS starters,
            SUM(pms.minutes_played) AS team_minutes
        FROM player_match_stats AS pms
        INNER JOIN teams AS t
            ON t.team_id = pms.team_id
        WHERE pms.match_id = ?
        GROUP BY
            pms.team_id,
            t.name
        ORDER BY pms.team_id
        """,
        (MATCH_ID,),
    ).fetchall()


def print_team_minutes(
    title: str,
    rows: list[sqlite3.Row],
) -> None:
    print()
    print(title)
    print("-" * 110)

    for row in rows:
        print(dict(row))


def validate_identity(
    connection: sqlite3.Connection,
) -> tuple[sqlite3.Row, sqlite3.Row]:
    source = get_player(
        connection,
        SOURCE_PLAYER_ID,
    )
    target = get_player(
        connection,
        TARGET_PLAYER_ID,
    )

    if source is None:
        raise RuntimeError(
            "Quellspieler 584 fehlt."
        )

    if target is None:
        raise RuntimeError(
            "Zielspieler 436 fehlt."
        )

    source_name = (
        (source["first_name"] or "").strip().casefold(),
        (source["last_name"] or "").strip().casefold(),
    )

    target_name = (
        (target["first_name"] or "").strip().casefold(),
        (target["last_name"] or "").strip().casefold(),
    )

    if source_name != target_name:
        raise RuntimeError(
            "Namen von Quelle und Ziel stimmen nicht überein."
        )

    source_event_teams = get_event_team_ids(
        connection,
        SOURCE_PLAYER_ID,
    )

    target_lineup_teams = get_lineup_team_ids(
        connection,
        TARGET_PLAYER_ID,
    )

    if source_event_teams != [2]:
        raise RuntimeError(
            "Quellspieler 584 gehört in Spiel 162 "
            "nicht eindeutig zu team_id=2."
        )

    if target_lineup_teams != [2]:
        raise RuntimeError(
            "Zielspieler 436 steht in Spiel 162 "
            "nicht eindeutig für team_id=2 im Lineup."
        )

    return (
        source,
        target,
    )


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 162 TESTMERGE V2 / "
        "LEON GERHARD 584 -> 436"
    )
    print("=" * 110)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Quelle fehlt: {SOURCE_DB}"
        )

    shutil.copy2(
        SOURCE_DB,
        TEST_DB,
    )

    print(f"Quelle:  {SOURCE_DB}")
    print(f"Test-DB: {TEST_DB}")
    print(
        "Haupt-DB wird NICHT verändert."
    )

    connection = sqlite3.connect(
        TEST_DB
    )
    connection.row_factory = sqlite3.Row

    try:
        repository = PlayerRepository(
            connection
        )

        source_before, target_before = (
            validate_identity(
                connection
            )
        )

        print()
        print("VOR MERGE")
        print("-" * 110)
        print(
            "Quelle:",
            row_dict(source_before),
        )
        print(
            "Ziel:  ",
            row_dict(target_before),
        )

        print()
        print("HISTORISCHE TEAM-PRÜFUNG SPIEL 162")
        print("-" * 110)
        print(
            "Quelle Event-Team-IDs:",
            get_event_team_ids(
                connection,
                SOURCE_PLAYER_ID,
            ),
        )
        print(
            "Ziel Lineup-Team-IDs:",
            get_lineup_team_ids(
                connection,
                TARGET_PLAYER_ID,
            ),
        )
        print(
            "Ergebnis: Beide repräsentieren in Spiel 162 "
            "team_id=2 (DJK St. Matthias Trier)."
        )

        print()
        print("ALIASE VORHER")
        print("-" * 110)
        print(
            "Quelle:",
            get_aliases(
                connection,
                SOURCE_PLAYER_ID,
            ),
        )
        print(
            "Ziel:  ",
            get_aliases(
                connection,
                TARGET_PLAYER_ID,
            ),
        )

        print_refs(
            "REFERENZEN QUELLSPIELER VORHER",
            get_match_refs(
                connection,
                SOURCE_PLAYER_ID,
            ),
        )

        print_refs(
            "REFERENZEN ZIELSPIELER VORHER",
            get_match_refs(
                connection,
                TARGET_PLAYER_ID,
            ),
        )

        print_team_minutes(
            "TEAM-MINUTEN VORHER",
            get_team_minutes(
                connection
            ),
        )

        print()
        print("TEST-NORMALISIERUNG")
        print("-" * 110)
        print(
            "Der Repository-Sicherheitscheck blockiert, "
            "weil players.team_id aktuell unterschiedlich ist."
        )
        print(
            "Für diesen TEST wird ausschließlich in der Test-DB "
            "source.team_id auf target.team_id gesetzt."
        )
        print(
            "Die historische Identität wurde vorher über Spiel 162 "
            "separat bestätigt."
        )

        connection.execute(
            """
            UPDATE players
            SET team_id = ?
            WHERE player_id = ?
            """,
            (
                int(
                    target_before["team_id"]
                ),
                SOURCE_PLAYER_ID,
            ),
        )
        connection.commit()

        normalized_source = get_player(
            connection,
            SOURCE_PLAYER_ID,
        )

        print(
            "Quelle nach Test-Normalisierung:",
            row_dict(normalized_source),
        )

        result_id = repository.merge_players(
            source_player_id=SOURCE_PLAYER_ID,
            target_player_id=TARGET_PLAYER_ID,
            commit=True,
        )

        print()
        print("MERGE")
        print("-" * 110)
        print(
            f"Rückgabe player_id: {result_id}"
        )

        source_after = get_player(
            connection,
            SOURCE_PLAYER_ID,
        )

        target_after = get_player(
            connection,
            TARGET_PLAYER_ID,
        )

        print()
        print("NACH MERGE")
        print("-" * 110)
        print(
            "Quelle:",
            row_dict(source_after),
        )
        print(
            "Ziel:  ",
            row_dict(target_after),
        )

        if source_after is not None:
            raise RuntimeError(
                "Quellspieler 584 wurde "
                "nicht entfernt."
            )

        print()
        print("ALIASE NACHHER")
        print("-" * 110)

        target_aliases = get_aliases(
            connection,
            TARGET_PLAYER_ID,
        )

        print(target_aliases)

        expected_aliases = {
            "020RH6CUOO000000VS541L4IVSG6F5RO",
            "030QEUB3PS000000VS5489BVVV6E165H",
            "030UUHC72S00000EVS5489C0VU570GJ0",
        }

        if not expected_aliases.issubset(
            set(target_aliases)
        ):
            raise RuntimeError(
                "Nicht alle Leon-Gerhard-Aliase "
                "wurden auf player_id 436 übertragen."
            )

        print_refs(
            "REFERENZEN ZIELSPIELER NACH MERGE",
            get_match_refs(
                connection,
                TARGET_PLAYER_ID,
            ),
        )

        builder = PlayerMatchStatsBuilder(
            connection
        )

        result = builder.build(
            MATCH_ID
        )

        print()
        print("BUILDERERGEBNIS")
        print("-" * 110)
        print(result)

        team_minutes = get_team_minutes(
            connection
        )

        print_team_minutes(
            "TEAM-MINUTEN NACH MERGE + REBUILD",
            team_minutes,
        )

        target_stat_rows = connection.execute(
            """
            SELECT
                pms.player_match_stat_id,
                pms.team_id,
                pms.player_id,
                p.first_name,
                p.last_name,
                pms.is_starting,
                pms.was_substituted_in,
                pms.was_substituted_out,
                pms.minute_in,
                pms.minute_out,
                pms.minutes_played
            FROM player_match_stats AS pms
            INNER JOIN players AS p
                ON p.player_id = pms.player_id
            WHERE
                pms.match_id = ?
                AND pms.player_id = ?
            ORDER BY
                pms.player_match_stat_id
            """,
            (
                MATCH_ID,
                TARGET_PLAYER_ID,
            ),
        ).fetchall()

        print()
        print("LEON GERHARD NACH REBUILD")
        print("-" * 110)

        for row in target_stat_rows:
            print(dict(row))

        if len(target_stat_rows) != 1:
            raise RuntimeError(
                "Leon Gerhard hat nach dem "
                "Rebuild nicht exakt eine "
                "Statistikzeile."
            )

        target_stat = target_stat_rows[0]

        if int(
            target_stat["is_starting"]
        ) != 1:
            raise RuntimeError(
                "Leon Gerhard ist nach Merge "
                "nicht mehr Starter."
            )

        if int(
            target_stat["was_substituted_out"]
        ) != 1:
            raise RuntimeError(
                "54'-Auswechslung wurde nicht "
                "auf den Starter übertragen."
            )

        if int(
            target_stat["minute_out"]
        ) != 54:
            raise RuntimeError(
                "minute_out von Leon Gerhard "
                "ist nicht 54."
            )

        if int(
            target_stat["minutes_played"]
        ) != 54:
            raise RuntimeError(
                "minutes_played von Leon Gerhard "
                "ist nicht 54."
            )

        djk_row = next(
            (
                row
                for row in team_minutes
                if row["team_name"]
                == "DJK St. Matthias Trier"
            ),
            None,
        )

        if djk_row is None:
            raise RuntimeError(
                "DJK-Teamzeile fehlt."
            )

        if int(
            djk_row["team_minutes"]
        ) != 990:
            raise RuntimeError(
                "DJK St. Matthias Trier landet "
                "nach Merge nicht bei 990 Minuten."
            )

        print()
        print("=" * 110)
        print(
            "ERGEBNIS: SPIEL 162 SAUBER."
        )
        print(
            "Leon Gerhard 584 -> 436 ist fachlich korrekt; "
            "Wechsel, Aliase und Team-Minuten stimmen."
        )
        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
