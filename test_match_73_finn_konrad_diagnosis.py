from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)


SOURCE_DB = Path("data/database/kreisligamanager.db")
TEST_DB = Path("data/database/match_73_finn_konrad_test.db")

MATCH_ID = 73
TEAM_NAME = "FSG Ehrang-Pfalzel"
PLAYER_NAME = ("Finn", "Konrad")


def get_team(connection: sqlite3.Connection) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            t.team_id,
            t.name
        FROM matches m
        JOIN teams t
          ON t.team_id IN (m.home_team_id, m.away_team_id)
        WHERE
            m.match_id = ?
            AND t.name = ?
        """,
        (MATCH_ID, TEAM_NAME),
    ).fetchone()

    if row is None:
        raise RuntimeError("Zielteam nicht gefunden.")

    return row


def get_player(connection: sqlite3.Connection) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            p.player_id,
            p.first_name,
            p.last_name,
            p.external_id
        FROM players p
        WHERE
            p.first_name = ?
            AND p.last_name = ?
        ORDER BY p.player_id
        """,
        PLAYER_NAME,
    ).fetchone()

    if row is None:
        raise RuntimeError("Finn Konrad nicht gefunden.")

    return row


def print_player_events(
    connection: sqlite3.Connection,
    player_id: int,
) -> None:
    rows = connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.team_id,
            e.player_id,
            e.related_player_id,
            p.first_name,
            p.last_name,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name
        FROM events e
        JOIN event_types et
          ON et.event_type_id = e.event_type_id
        LEFT JOIN players p
          ON p.player_id = e.player_id
        LEFT JOIN players rp
          ON rp.player_id = e.related_player_id
        WHERE
            e.match_id = ?
            AND (
                e.player_id = ?
                OR e.related_player_id = ?
            )
        ORDER BY e.minute, e.event_id
        """,
        (MATCH_ID, player_id, player_id),
    ).fetchall()

    for row in rows:
        print(dict(row))


def print_team_substitutions(
    connection: sqlite3.Connection,
    team_id: int,
) -> None:
    rows = connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name
        FROM events e
        JOIN event_types et
          ON et.event_type_id = e.event_type_id
        LEFT JOIN players p
          ON p.player_id = e.player_id
        LEFT JOIN players rp
          ON rp.player_id = e.related_player_id
        WHERE
            e.match_id = ?
            AND e.team_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY e.minute, e.event_id
        """,
        (MATCH_ID, team_id),
    ).fetchall()

    for row in rows:
        print(dict(row))


def get_player_stat(
    connection: sqlite3.Connection,
    player_id: int,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            pms.player_match_stat_id,
            pms.player_id,
            p.first_name,
            p.last_name,
            pms.is_starting,
            pms.was_substituted_in,
            pms.was_substituted_out,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played
        FROM player_match_stats pms
        JOIN players p
          ON p.player_id = pms.player_id
        WHERE
            pms.match_id = ?
            AND pms.player_id = ?
        """,
        (MATCH_ID, player_id),
    ).fetchone()


def get_team_minutes(
    connection: sqlite3.Connection,
    team_id: int,
) -> int:
    value = connection.execute(
        """
        SELECT COALESCE(SUM(minutes_played), 0)
        FROM player_match_stats
        WHERE
            match_id = ?
            AND team_id = ?
        """,
        (MATCH_ID, team_id),
    ).fetchone()[0]

    return int(value)


def get_duplicate_player_names(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            LOWER(TRIM(COALESCE(p.first_name, ''))) AS first_name_norm,
            LOWER(TRIM(COALESCE(p.last_name, ''))) AS last_name_norm,
            COUNT(DISTINCT p.player_id) AS player_count,
            GROUP_CONCAT(DISTINCT p.player_id) AS player_ids
        FROM player_match_stats pms
        JOIN players p
          ON p.player_id = pms.player_id
        WHERE pms.match_id = ?
        GROUP BY
            first_name_norm,
            last_name_norm
        HAVING COUNT(DISTINCT p.player_id) > 1
        ORDER BY player_count DESC
        """,
        (MATCH_ID,),
    ).fetchall()


def main() -> None:
    print("=" * 110)
    print("SPIEL 73 / FINN KONRAD - RÜCK-/MEHRFACHWECHSEL-DIAGNOSE")
    print("=" * 110)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Haupt-DB fehlt: {SOURCE_DB}")

    shutil.copy2(SOURCE_DB, TEST_DB)

    print(f"Quelle:  {SOURCE_DB}")
    print(f"Test-DB: {TEST_DB}")
    print("Haupt-DB wird NICHT verändert.")

    connection = sqlite3.connect(TEST_DB)
    connection.row_factory = sqlite3.Row

    try:
        team = get_team(connection)
        player = get_player(connection)

        print()
        print("TEAM / SPIELER")
        print("-" * 110)
        print(dict(team))
        print(dict(player))

        print()
        print("FINN-KONRAD-EVENTS")
        print("-" * 110)
        print_player_events(
            connection,
            int(player["player_id"]),
        )

        print()
        print("ALLE FSG-WECHSEL")
        print("-" * 110)
        print_team_substitutions(
            connection,
            int(team["team_id"]),
        )

        print()
        print("DOPPELTE NAMEN / PLAYER-IDs IN SPIEL 73")
        print("-" * 110)
        duplicates = get_duplicate_player_names(connection)

        if not duplicates:
            print("(keine)")
        else:
            for row in duplicates:
                print(dict(row))

        print()
        print("VOR REBUILD")
        print("-" * 110)
        stat_before = get_player_stat(
            connection,
            int(player["player_id"]),
        )
        print(
            dict(stat_before)
            if stat_before is not None
            else "(keine Statistik)"
        )
        print(
            f"FSG Team-Minuten: "
            f"{get_team_minutes(connection, int(team['team_id']))}"
        )

        builder = PlayerMatchStatsBuilder(connection)
        result = builder.build(MATCH_ID)

        print()
        print("BUILDERERGEBNIS")
        print("-" * 110)
        print(result)

        print()
        print("NACH REBUILD")
        print("-" * 110)
        stat_after = get_player_stat(
            connection,
            int(player["player_id"]),
        )
        print(
            dict(stat_after)
            if stat_after is not None
            else "(keine Statistik)"
        )

        team_minutes = get_team_minutes(
            connection,
            int(team["team_id"]),
        )
        print(f"FSG Team-Minuten: {team_minutes}")

        print()
        print("=" * 110)
        print("DIAGNOSE")
        print("=" * 110)

        if stat_after is None:
            raise RuntimeError(
                "Finn Konrad besitzt nach Rebuild keine Statistik."
            )

        events = connection.execute(
            """
            SELECT
                et.code,
                e.minute,
                e.player_id,
                e.related_player_id
            FROM events e
            JOIN event_types et
              ON et.event_type_id = e.event_type_id
            WHERE
                e.match_id = ?
                AND (
                    e.player_id = ?
                    OR e.related_player_id = ?
                )
                AND et.code IN (
                    'SUBSTITUTION_IN',
                    'SUBSTITUTION_OUT'
                )
            ORDER BY e.minute, e.event_id
            """,
            (
                MATCH_ID,
                int(player["player_id"]),
                int(player["player_id"]),
            ),
        ).fetchall()

        in_minutes = sorted(
            int(row["minute"])
            for row in events
            if row["code"] == "SUBSTITUTION_IN"
            and row["player_id"] == player["player_id"]
        )

        out_minutes = sorted(
            int(row["minute"])
            for row in events
            if row["code"] == "SUBSTITUTION_OUT"
            and row["player_id"] == player["player_id"]
        )

        related_in_minutes = sorted(
            int(row["minute"])
            for row in events
            if row["code"] == "SUBSTITUTION_IN"
            and row["related_player_id"] == player["player_id"]
        )

        related_out_minutes = sorted(
            int(row["minute"])
            for row in events
            if row["code"] == "SUBSTITUTION_OUT"
            and row["related_player_id"] == player["player_id"]
        )

        print(f"Direkte IN-Minuten:      {in_minutes}")
        print(f"Direkte OUT-Minuten:     {out_minutes}")
        print(f"Als Partner bei IN:      {related_in_minutes}")
        print(f"Als Partner bei OUT:     {related_out_minutes}")
        print(
            f"Builder-Minuten Finn:    "
            f"{stat_after['minutes_played']}"
        )
        print(
            f"Team-Minuten FSG:        "
            f"{team_minutes}"
        )

        if in_minutes == [71, 86]:
            print()
            print(
                "BEFUND: Finn Konrad besitzt zwei SUBSTITUTION_IN-Events "
                "(71' und 86')."
            )
            print(
                "Damit muss geprüft werden, ob zwischen 71' und 86' ein "
                "SUBSTITUTION_OUT für Finn fehlt oder ob das 86'-Event "
                "quell-/importseitig falsch zugeordnet ist."
            )
        elif len(in_minutes) > 1:
            print()
            print(
                "BEFUND: Mehrere direkte SUBSTITUTION_IN-Events für Finn Konrad."
            )
        else:
            print()
            print(
                "BEFUND: Die erwartete Doppel-IN-Konstellation liegt so nicht vor."
            )

        print()
        print(
            "Noch KEINE Datenänderung. "
            "Dieser Test bestimmt ausschließlich die Ursache."
        )
        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
