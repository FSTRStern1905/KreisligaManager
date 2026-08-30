from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")

CASES = (
    (50, "Nico", "Herz"),
    (76, "Tobias", "Marmann"),
    (109, "Dreni", "Mehani"),
    (122, "Philipp", "Salm"),
    (139, "Luca", "Klupsch"),
    (141, "Nico", "Herz"),
    (141, "Leon", "Klupsch"),
    (157, "Marius", "Jost"),
    (157, "Nicolas", "Hengel"),
    (181, "Joah", "Wallerius"),
    (181, "Kader", "Toure"),
)


def get_player(
    connection: sqlite3.Connection,
    first_name: str,
    last_name: str,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            player_id,
            first_name,
            last_name,
            external_id
        FROM players
        WHERE first_name = ?
          AND last_name = ?
        LIMIT 1
        """,
        (
            first_name,
            last_name,
        ),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Spieler nicht gefunden: "
            f"{first_name} {last_name}"
        )

    return row


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
        LIMIT 1
        """,
        (match_id,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Spiel nicht gefunden: {match_id}"
        )

    return row


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
        WHERE match_id = ?
          AND player_id = ?
        ORDER BY lineup_id
        """,
        (
            match_id,
            player_id,
        ),
    ).fetchall()


def get_stat_rows(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
) -> list[sqlite3.Row]:
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
            yellow_red_cards,
            red_cards
        FROM player_match_stats
        WHERE match_id = ?
          AND player_id = ?
        ORDER BY player_match_stat_id
        """,
        (
            match_id,
            player_id,
        ),
    ).fetchall()


def get_event_rows(
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
            p.first_name,
            p.last_name,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name
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


def print_rows(
    title: str,
    rows: list[sqlite3.Row],
) -> None:
    print()
    print(title)
    print("-" * 100)

    if not rows:
        print("(keine)")
        return

    for row in rows:
        print(dict(row))


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        print("=" * 100)
        print("MINUTEN-PROBLEMFÄLLE / SAMMELDIAGNOSE")
        print("=" * 100)

        for (
            match_id,
            first_name,
            last_name,
        ) in CASES:
            player = get_player(
                connection,
                first_name,
                last_name,
            )

            match = get_match(
                connection,
                match_id,
            )

            player_id = int(
                player["player_id"]
            )

            stat_rows = get_stat_rows(
                connection,
                match_id,
                player_id,
            )

            team_id = None

            if stat_rows:
                team_id = stat_rows[0]["team_id"]

            if team_id is None:
                lineup_rows = get_lineup_rows(
                    connection,
                    match_id,
                    player_id,
                )

                if lineup_rows:
                    team_id = lineup_rows[0]["team_id"]

            print()
            print("=" * 100)
            print(
                f"SPIEL {match_id} | "
                f"{first_name} {last_name}"
            )
            print("=" * 100)

            print("MATCH")
            print("-" * 100)
            print(dict(match))

            print()
            print("PLAYER")
            print("-" * 100)
            print(dict(player))

            print_rows(
                "LINEUPS",
                get_lineup_rows(
                    connection,
                    match_id,
                    player_id,
                ),
            )

            print_rows(
                "PLAYER_MATCH_STATS",
                stat_rows,
            )

            print_rows(
                "EVENTS MIT SPIELERBEZUG",
                get_event_rows(
                    connection,
                    match_id,
                    player_id,
                ),
            )

            if team_id is not None:
                print_rows(
                    "ALLE WECHSEL DES TEAMS",
                    get_team_substitution_rows(
                        connection,
                        match_id,
                        int(team_id),
                    ),
                )

        print()
        print("=" * 100)
        print("ENDE SAMMELDIAGNOSE")
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
