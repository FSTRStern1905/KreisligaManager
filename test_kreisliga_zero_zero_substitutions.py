from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

COMPETITION_ID = 1


def find_suspicious_cases(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.player_match_stat_id,
            pms.match_id,
            pms.team_id,
            pms.player_id,
            p.first_name,
            p.last_name,
            p.external_id,
            pms.is_starting,
            pms.was_substituted_in,
            pms.was_substituted_out,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played,
            m.matchday,
            m.external_id AS match_external_id,
            ht.name AS home_team,
            at.name AS away_team,
            t.name AS team_name
        FROM player_match_stats AS pms

        INNER JOIN players AS p
            ON p.player_id = pms.player_id

        INNER JOIN matches AS m
            ON m.match_id = pms.match_id

        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id

        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id

        INNER JOIN teams AS t
            ON t.team_id = pms.team_id

        WHERE
            m.competition_id = ?
            AND pms.is_starting = 0
            AND pms.was_substituted_in = 1
            AND pms.was_substituted_out = 1
            AND pms.minute_in = 0
            AND pms.minute_out = 0
            AND pms.minutes_played > 0

        ORDER BY
            pms.match_id,
            pms.team_id,
            pms.player_id
        """,
        (COMPETITION_ID,),
    ).fetchall()


def get_lineup_rows(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            lineup_id,
            match_id,
            team_id,
            player_id,
            is_starting,
            shirt_number,
            position
        FROM lineups
        WHERE
            match_id = ?
            AND player_id = ?
        ORDER BY lineup_id
        """,
        (
            match_id,
            player_id,
        ),
    ).fetchall()


def get_player_event_rows(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.team_id,
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name,
            e.notes
        FROM events AS e

        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id

        LEFT JOIN players AS p
            ON p.player_id = e.player_id

        LEFT JOIN players AS rp
            ON rp.player_id = e.related_player_id

        WHERE
            e.match_id = ?
            AND (
                e.player_id = ?
                OR e.related_player_id = ?
            )

        ORDER BY
            e.minute,
            e.event_id
        """,
        (
            match_id,
            player_id,
            player_id,
        ),
    ).fetchall()


def get_team_substitution_rows(
    connection: sqlite3.Connection,
    match_id: int,
    team_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.team_id,
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name,
            e.notes
        FROM events AS e

        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id

        LEFT JOIN players AS p
            ON p.player_id = e.player_id

        LEFT JOIN players AS rp
            ON rp.player_id = e.related_player_id

        WHERE
            e.match_id = ?
            AND e.team_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )

        ORDER BY
            e.minute,
            e.event_id
        """,
        (
            match_id,
            team_id,
        ),
    ).fetchall()


def get_related_counterparts(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT DISTINCT
            p.player_id,
            p.first_name,
            p.last_name,
            p.external_id
        FROM players AS p
        WHERE p.player_id IN (
            SELECT e.related_player_id
            FROM events AS e
            WHERE
                e.match_id = ?
                AND e.player_id = ?
                AND e.related_player_id IS NOT NULL

            UNION

            SELECT e.player_id
            FROM events AS e
            WHERE
                e.match_id = ?
                AND e.related_player_id = ?
                AND e.player_id IS NOT NULL
        )
        ORDER BY
            p.last_name,
            p.first_name
        """,
        (
            match_id,
            player_id,
            match_id,
            player_id,
        ),
    ).fetchall()


def print_rows(
    title: str,
    rows: list[sqlite3.Row],
) -> None:
    print()
    print(title)
    print("-" * 110)

    if not rows:
        print("(keine)")
        return

    for row in rows:
        print(dict(row))


def player_name(
    row: sqlite3.Row,
) -> str:
    name = (
        f"{row['first_name'] or ''} "
        f"{row['last_name'] or ''}"
    ).strip()

    return name or f"player_id={row['player_id']}"


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        cases = find_suspicious_cases(
            connection
        )

        print("=" * 110)
        print(
            "KREISLIGA A7: DIAGNOSE "
            "0'->0'-BANKSPIELER MIT POSITIVEN MINUTEN"
        )
        print("=" * 110)
        print(f"Datenbank: {DB_PATH}")
        print(
            f"Wettbewerb: competition_id="
            f"{COMPETITION_ID}"
        )
        print(
            "Haupt-DB wird NICHT verändert."
        )
        print(
            f"Gefundene Fälle: {len(cases)}"
        )

        if not cases:
            print()
            print(
                "STATUS: Keine verdächtigen "
                "0'->0'-Bankspieler gefunden."
            )
            return

        for case in cases:
            match_id = int(
                case["match_id"]
            )
            team_id = int(
                case["team_id"]
            )
            player_id = int(
                case["player_id"]
            )

            print()
            print("=" * 110)
            print(
                f"SPIEL {match_id} | "
                f"ST {case['matchday']} | "
                f"{case['home_team']} - "
                f"{case['away_team']}"
            )
            print("=" * 110)

            print(
                f"SPIELER: {player_name(case)}"
            )
            print(
                f"TEAM:    {case['team_name']}"
            )
            print(
                f"PLAYER_ID:   {player_id}"
            )
            print(
                f"EXTERNAL_ID: "
                f"{case['external_id']}"
            )
            print(
                f"MATCH_EXT_ID: "
                f"{case['match_external_id']}"
            )

            print()
            print("PLAYER_MATCH_STATS")
            print("-" * 110)
            print(
                {
                    "player_match_stat_id": case[
                        "player_match_stat_id"
                    ],
                    "match_id": match_id,
                    "team_id": team_id,
                    "player_id": player_id,
                    "is_starting": case[
                        "is_starting"
                    ],
                    "was_substituted_in": case[
                        "was_substituted_in"
                    ],
                    "was_substituted_out": case[
                        "was_substituted_out"
                    ],
                    "minute_in": case[
                        "minute_in"
                    ],
                    "minute_out": case[
                        "minute_out"
                    ],
                    "minutes_played": case[
                        "minutes_played"
                    ],
                }
            )

            print_rows(
                "LINEUPS",
                get_lineup_rows(
                    connection,
                    match_id,
                    player_id,
                ),
            )

            print_rows(
                "EVENTS MIT SPIELERBEZUG "
                "(player_id ODER related_player_id)",
                get_player_event_rows(
                    connection,
                    match_id,
                    player_id,
                ),
            )

            print_rows(
                "VERKNÜPFTE WECHSELPARTNER",
                get_related_counterparts(
                    connection,
                    match_id,
                    player_id,
                ),
            )

            print_rows(
                "ALLE WECHSEL DES TEAMS",
                get_team_substitution_rows(
                    connection,
                    match_id,
                    team_id,
                ),
            )

        print()
        print("=" * 110)
        print("GESAMTERGEBNIS")
        print("=" * 110)
        print(
            f"Verdächtige Kreisliga-Fälle: "
            f"{len(cases)}"
        )
        print(
            "Diagnose abgeschlossen. "
            "Es wurden keine Daten verändert."
        )
        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
