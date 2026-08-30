from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(
    "data/database/player_match_stats_builder_interval_test.db"
)

MATCH_IDS = (
    73,
    74,
    141,
    162,
)


def player_name(
    first_name: str | None,
    last_name: str | None,
    player_id: int | None,
) -> str:
    name = (
        f"{first_name or ''} "
        f"{last_name or ''}"
    ).strip()

    if name:
        return name

    if player_id is None:
        return "?"

    return f"player_id={player_id}"


def get_match(
    connection: sqlite3.Connection,
    match_id: int,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            m.match_id,
            m.matchday,
            m.external_id,
            m.home_team_id,
            m.away_team_id,
            ht.name AS home_team,
            at.name AS away_team
        FROM matches AS m
        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id
        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id
        WHERE m.match_id = ?
        """,
        (match_id,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Spiel {match_id} nicht gefunden."
        )

    return row


def get_lineups(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            l.lineup_id,
            l.match_id,
            l.team_id,
            t.name AS team_name,
            l.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            l.is_starting,
            l.shirt_number,
            l.position
        FROM lineups AS l
        INNER JOIN teams AS t
            ON t.team_id = l.team_id
        INNER JOIN players AS p
            ON p.player_id = l.player_id
        WHERE l.match_id = ?
        ORDER BY
            l.team_id,
            l.is_starting DESC,
            l.player_id
        """,
        (match_id,),
    ).fetchall()


def get_stats(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.player_match_stat_id,
            pms.match_id,
            pms.team_id,
            t.name AS team_name,
            pms.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            pms.is_starting,
            pms.was_substituted_in,
            pms.was_substituted_out,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played
        FROM player_match_stats AS pms
        INNER JOIN teams AS t
            ON t.team_id = pms.team_id
        INNER JOIN players AS p
            ON p.player_id = pms.player_id
        WHERE pms.match_id = ?
        ORDER BY
            pms.team_id,
            pms.is_starting DESC,
            pms.player_id
        """,
        (match_id,),
    ).fetchall()


def get_events(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            e.event_id,
            e.match_id,
            e.team_id,
            t.name AS team_name,
            et.code,
            e.minute,
            e.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            e.related_player_id,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name,
            rp.external_id AS related_external_id,
            e.notes
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN teams AS t
            ON t.team_id = e.team_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        LEFT JOIN players AS rp
            ON rp.player_id = e.related_player_id
        WHERE e.match_id = ?
        ORDER BY
            e.minute,
            e.event_id
        """,
        (match_id,),
    ).fetchall()


def get_duplicate_stat_players(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            COUNT(*) AS count_rows
        FROM player_match_stats AS pms
        INNER JOIN players AS p
            ON p.player_id = pms.player_id
        WHERE pms.match_id = ?
        GROUP BY
            pms.player_id,
            p.first_name,
            p.last_name,
            p.external_id
        HAVING COUNT(*) > 1
        ORDER BY count_rows DESC
        """,
        (match_id,),
    ).fetchall()


def get_same_name_different_ids(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            p.first_name,
            p.last_name,
            GROUP_CONCAT(
                DISTINCT p.player_id
            ) AS player_ids,
            GROUP_CONCAT(
                DISTINCT p.external_id
            ) AS external_ids,
            COUNT(
                DISTINCT p.player_id
            ) AS distinct_players
        FROM (
            SELECT player_id
            FROM lineups
            WHERE match_id = ?

            UNION ALL

            SELECT player_id
            FROM player_match_stats
            WHERE match_id = ?

            UNION ALL

            SELECT player_id
            FROM events
            WHERE match_id = ?
              AND player_id IS NOT NULL
        ) AS src
        INNER JOIN players AS p
            ON p.player_id = src.player_id
        GROUP BY
            p.first_name,
            p.last_name
        HAVING COUNT(
            DISTINCT p.player_id
        ) > 1
        ORDER BY
            p.last_name,
            p.first_name
        """,
        (
            match_id,
            match_id,
            match_id,
        ),
    ).fetchall()


def print_lineups(
    rows: list[sqlite3.Row],
) -> None:
    print()
    print("LINEUPS")
    print("-" * 120)

    for row in rows:
        print(
            f"team={row['team_name']:<28} "
            f"player_id={row['player_id']:<4} "
            f"ext={row['external_id']} | "
            f"{player_name(row['first_name'], row['last_name'], row['player_id']):<30} "
            f"starter={row['is_starting']} "
            f"nr={row['shirt_number']} "
            f"pos={row['position']}"
        )


def print_stats(
    rows: list[sqlite3.Row],
) -> None:
    print()
    print("PLAYER_MATCH_STATS")
    print("-" * 120)

    for row in rows:
        print(
            f"team={row['team_name']:<28} "
            f"player_id={row['player_id']:<4} "
            f"ext={row['external_id']} | "
            f"{player_name(row['first_name'], row['last_name'], row['player_id']):<30} "
            f"starter={row['is_starting']} "
            f"IN={row['was_substituted_in']} "
            f"OUT={row['was_substituted_out']} "
            f"in={row['minute_in']} "
            f"out={row['minute_out']} "
            f"min={row['minutes_played']}"
        )


def print_events(
    rows: list[sqlite3.Row],
) -> None:
    print()
    print("ALLE EVENTS")
    print("-" * 120)

    for row in rows:
        print(
            f"id={row['event_id']:<5} "
            f"{str(row['minute']) + chr(39):<5} "
            f"{row['code']:<20} "
            f"team={str(row['team_name']):<28} "
            f"player_id={str(row['player_id']):<4} "
            f"{player_name(row['first_name'], row['last_name'], row['player_id'])}"
            f" ↔ "
            f"{player_name(row['related_first_name'], row['related_last_name'], row['related_player_id'])}"
        )


def print_special_checks(
    connection: sqlite3.Connection,
    match_id: int,
) -> None:
    duplicates = get_duplicate_stat_players(
        connection,
        match_id,
    )

    same_name_ids = get_same_name_different_ids(
        connection,
        match_id,
    )

    print()
    print("DUPLIKAT-/ID-PRÜFUNG")
    print("-" * 120)

    if not duplicates:
        print(
            "Mehrfache player_match_stats-Zeilen "
            "für dieselbe player_id: keine"
        )
    else:
        print(
            "Mehrfache player_match_stats-Zeilen:"
        )

        for row in duplicates:
            print(dict(row))

    if not same_name_ids:
        print(
            "Gleicher Name mit mehreren player_ids: "
            "keine"
        )
    else:
        print(
            "Gleicher Name mit mehreren player_ids:"
        )

        for row in same_name_ids:
            print(dict(row))


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Test-DB nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        print("=" * 120)
        print(
            "KREISLIGA A7: SAMMELDIAGNOSE "
            "RESTFÄLLE 73 / 74 / 141 / 162"
        )
        print("=" * 120)
        print(f"Datenbank: {DB_PATH}")
        print(
            "Haupt-DB wird NICHT verändert."
        )

        for match_id in MATCH_IDS:
            match = get_match(
                connection,
                match_id,
            )

            print()
            print("=" * 120)
            print(
                f"SPIEL {match_id} | "
                f"ST {match['matchday']} | "
                f"{match['home_team']} - "
                f"{match['away_team']}"
            )
            print("=" * 120)
            print(
                f"external_id: "
                f"{match['external_id']}"
            )

            print_lineups(
                get_lineups(
                    connection,
                    match_id,
                )
            )

            print_stats(
                get_stats(
                    connection,
                    match_id,
                )
            )

            print_events(
                get_events(
                    connection,
                    match_id,
                )
            )

            print_special_checks(
                connection,
                match_id,
            )

        print()
        print("=" * 120)
        print("DIAGNOSE ABGESCHLOSSEN")
        print("=" * 120)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
