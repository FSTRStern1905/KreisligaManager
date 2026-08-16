from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_CANDIDATES = (
    Path("data/database/kreisligamanager.db"),
    Path("data/kreisligamanager.db"),
    Path("kreisligamanager.db"),
)


def find_database() -> Path:
    for path in DB_CANDIDATES:
        if path.exists():
            return path

    raise FileNotFoundError(
        "KreisligaManager-Datenbank nicht gefunden."
    )


def table_exists(
    connection: sqlite3.Connection,
    table: str,
) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (table,),
    ).fetchone()

    return row is not None


def columns(
    connection: sqlite3.Connection,
    table: str,
) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }


def first_existing(
    options: tuple[str, ...],
    available: set[str],
) -> str | None:
    for option in options:
        if option in available:
            return option

    return None


def player_name_expr(
    player_columns: set[str],
    alias: str,
) -> str:
    if {
        "first_name",
        "last_name",
    } <= player_columns:
        return (
            f"TRIM("
            f"COALESCE({alias}.first_name, '') "
            f"|| ' ' || "
            f"COALESCE({alias}.last_name, '')"
            f")"
        )

    if "name" in player_columns:
        return (
            f"COALESCE({alias}.name, '')"
        )

    return "''"


def main() -> None:
    db_path = find_database()

    connection = sqlite3.connect(
        db_path
    )
    connection.row_factory = sqlite3.Row

    required_tables = {
        "matches",
        "events",
        "event_types",
        "teams",
        "players",
    }

    missing_tables = [
        table
        for table in required_tables
        if not table_exists(
            connection,
            table,
        )
    ]

    if missing_tables:
        raise RuntimeError(
            "Fehlende Tabellen: "
            + ", ".join(
                missing_tables
            )
        )

    match_columns = columns(
        connection,
        "matches",
    )
    event_columns = columns(
        connection,
        "events",
    )
    event_type_columns = columns(
        connection,
        "event_types",
    )
    team_columns = columns(
        connection,
        "teams",
    )
    player_columns = columns(
        connection,
        "players",
    )

    event_id_column = first_existing(
        (
            "event_id",
            "id",
        ),
        event_columns,
    )

    event_type_id_column = first_existing(
        (
            "event_type_id",
        ),
        event_columns,
    )

    event_type_pk_column = first_existing(
        (
            "event_type_id",
            "id",
        ),
        event_type_columns,
    )

    event_type_code_column = first_existing(
        (
            "code",
            "event_type_code",
            "name",
        ),
        event_type_columns,
    )

    minute_column = first_existing(
        ("minute",),
        event_columns,
    )

    team_id_column = first_existing(
        ("team_id",),
        event_columns,
    )

    player_id_column = first_existing(
        ("player_id",),
        event_columns,
    )

    related_player_id_column = (
        first_existing(
            (
                "related_player_id",
            ),
            event_columns,
        )
    )

    notes_column = first_existing(
        (
            "notes",
            "description",
        ),
        event_columns,
    )

    value_column = first_existing(
        ("value",),
        event_columns,
    )

    home_team_column = first_existing(
        ("home_team_id",),
        match_columns,
    )

    away_team_column = first_existing(
        ("away_team_id",),
        match_columns,
    )

    team_name_column = first_existing(
        (
            "name",
            "team_name",
            "short_name",
        ),
        team_columns,
    )

    required_columns = {
        "events.event_type_id":
            event_type_id_column,
        "event_types PK":
            event_type_pk_column,
        "event_types.code":
            event_type_code_column,
        "matches.home_team_id":
            home_team_column,
        "matches.away_team_id":
            away_team_column,
        "teams.name":
            team_name_column,
    }

    missing_columns = [
        label
        for label, value
        in required_columns.items()
        if value is None
    ]

    if missing_columns:
        raise RuntimeError(
            "Benötigte Spalten fehlen: "
            + ", ".join(
                missing_columns
            )
        )

    player_name = player_name_expr(
        player_columns,
        "p",
    )

    related_player_name = (
        player_name_expr(
            player_columns,
            "rp",
        )
    )

    select_parts = [
        "e.match_id AS match_id",
        (
            f"et.{event_type_code_column} "
            f"AS event_type"
        ),
        (
            f"e.{event_id_column} "
            f"AS event_id"
            if event_id_column
            else "NULL AS event_id"
        ),
        (
            f"e.{minute_column} "
            f"AS minute"
            if minute_column
            else "NULL AS minute"
        ),
        (
            f"e.{team_id_column} "
            f"AS team_id"
            if team_id_column
            else "NULL AS team_id"
        ),
        (
            f"e.{player_id_column} "
            f"AS player_id"
            if player_id_column
            else "NULL AS player_id"
        ),
        (
            f"e.{related_player_id_column} "
            f"AS related_player_id"
            if related_player_id_column
            else "NULL AS related_player_id"
        ),
        (
            f"e.{notes_column} "
            f"AS notes"
            if notes_column
            else "'' AS notes"
        ),
        (
            f"e.{value_column} "
            f"AS value"
            if value_column
            else "'' AS value"
        ),
        (
            f"{player_name} "
            f"AS player_name"
        ),
        (
            f"{related_player_name} "
            f"AS related_player_name"
        ),
        (
            f"ht.{team_name_column} "
            f"AS home_team"
        ),
        (
            f"at.{team_name_column} "
            f"AS away_team"
        ),
    ]

    joins = [
        (
            "INNER JOIN event_types et "
            f"ON et.{event_type_pk_column} "
            f"= e.{event_type_id_column}"
        ),
        (
            "INNER JOIN matches m "
            "ON m.match_id = e.match_id"
        ),
        (
            "LEFT JOIN teams ht "
            f"ON ht.team_id = "
            f"m.{home_team_column}"
        ),
        (
            "LEFT JOIN teams at "
            f"ON at.team_id = "
            f"m.{away_team_column}"
        ),
    ]

    if player_id_column:
        joins.append(
            "LEFT JOIN players p "
            f"ON p.player_id = "
            f"e.{player_id_column}"
        )
    else:
        joins.append(
            "LEFT JOIN players p "
            "ON 1 = 0"
        )

    if related_player_id_column:
        joins.append(
            "LEFT JOIN players rp "
            f"ON rp.player_id = "
            f"e.{related_player_id_column}"
        )
    else:
        joins.append(
            "LEFT JOIN players rp "
            "ON 1 = 0"
        )

    order_minute = (
        f"COALESCE(e.{minute_column}, 0)"
        if minute_column
        else "0"
    )

    sql = f"""
        SELECT
            {", ".join(select_parts)}
        FROM events e
        {" ".join(joins)}
        WHERE
            UPPER(
                et.{event_type_code_column}
            ) IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY
            e.match_id,
            {order_minute},
            et.{event_type_code_column},
            e.rowid
    """

    rows = connection.execute(
        sql
    ).fetchall()

    by_match: dict[
        int,
        list[sqlite3.Row],
    ] = defaultdict(list)

    for row in rows:
        by_match[
            int(row["match_id"])
        ].append(
            row
        )

    print("=" * 120)
    print(
        "MASSENDIAGNOSE WECHSEL"
    )
    print("=" * 120)
    print(
        f"Datenbank: {db_path}"
    )
    print(
        "Spiele mit Wechsel-Events: "
        f"{len(by_match)}"
    )
    print(
        "Wechsel-Eventzeilen:       "
        f"{len(rows)}"
    )

    suspicious_matches = 0
    total_in = 0
    total_out = 0
    incomplete_events = 0
    unpaired_groups = 0

    for (
        match_id,
        events,
    ) in by_match.items():

        substitution_in = [
            row
            for row in events
            if str(
                row["event_type"]
            ).upper()
            == "SUBSTITUTION_IN"
        ]

        substitution_out = [
            row
            for row in events
            if str(
                row["event_type"]
            ).upper()
            == "SUBSTITUTION_OUT"
        ]

        total_in += len(
            substitution_in
        )
        total_out += len(
            substitution_out
        )

        groups: dict[
            tuple,
            list[sqlite3.Row],
        ] = defaultdict(list)

        for row in events:
            key = (
                row["minute"],
                row["team_id"],
                str(
                    row["notes"] or ""
                ).strip(),
            )

            groups[key].append(
                row
            )

        bad_groups = []

        for (
            key,
            group,
        ) in groups.items():

            group_in = sum(
                1
                for row in group
                if str(
                    row["event_type"]
                ).upper()
                == "SUBSTITUTION_IN"
            )

            group_out = sum(
                1
                for row in group
                if str(
                    row["event_type"]
                ).upper()
                == "SUBSTITUTION_OUT"
            )

            if (
                group_in != 1
                or group_out != 1
            ):
                bad_groups.append(
                    (
                        key,
                        group,
                        group_in,
                        group_out,
                    )
                )

        incomplete = [
            row
            for row in events
            if (
                row["team_id"]
                is None
                or row["player_id"]
                is None
                or row[
                    "related_player_id"
                ]
                is None
            )
        ]

        if (
            len(substitution_in)
            == len(substitution_out)
            and not bad_groups
            and not incomplete
        ):
            continue

        suspicious_matches += 1
        incomplete_events += len(
            incomplete
        )
        unpaired_groups += len(
            bad_groups
        )

        first = events[0]

        print()
        print("=" * 120)
        print(
            f"SPIEL {match_id}: "
            f"{first['home_team'] or '?'} "
            f"- "
            f"{first['away_team'] or '?'}"
        )
        print("=" * 120)

        print(
            "SUBSTITUTION_IN:  "
            f"{len(substitution_in)} | "
            "SUBSTITUTION_OUT: "
            f"{len(substitution_out)} | "
            "unvollständig: "
            f"{len(incomplete)} | "
            "auffällige Wechselgruppen: "
            f"{len(bad_groups)}"
        )

        for (
            key,
            group,
            group_in,
            group_out,
        ) in bad_groups:

            minute, team_id, notes = key

            print("-" * 120)
            print(
                f"{minute}' | "
                f"team_id={team_id} | "
                f"IN={group_in} "
                f"OUT={group_out}"
            )

            if notes:
                print(
                    f"Beschreibung: "
                    f"{notes}"
                )

            for row in group:
                print(
                    f"  "
                    f"{str(row['event_type']):18} | "
                    f"player_id="
                    f"{row['player_id']} "
                    f"({row['player_name'] or '-'}) | "
                    f"related="
                    f"{row['related_player_id']} "
                    f"({row['related_player_name'] or '-'}) | "
                    f"event_id="
                    f"{row['event_id']}"
                )

                if row["value"]:
                    print(
                        f"    value: "
                        f"{row['value']}"
                    )

        if incomplete:
            print("-" * 120)
            print(
                "UNVOLLSTÄNDIGE EVENT-ZEILEN"
            )

            for row in incomplete:
                print(
                    f"  {row['minute']}' | "
                    f"{row['event_type']} | "
                    f"team_id="
                    f"{row['team_id']} | "
                    f"player_id="
                    f"{row['player_id']} "
                    f"({row['player_name'] or '-'}) | "
                    f"related="
                    f"{row['related_player_id']} "
                    f"({row['related_player_name'] or '-'})"
                )

                if row["notes"]:
                    print(
                        f"    "
                        f"{row['notes']}"
                    )

    print()
    print("=" * 120)
    print(
        "ZUSAMMENFASSUNG"
    )
    print("=" * 120)
    print(
        "SUBSTITUTION_IN gesamt:      "
        f"{total_in}"
    )
    print(
        "SUBSTITUTION_OUT gesamt:     "
        f"{total_out}"
    )
    print(
        "Auffällige Spiele:           "
        f"{suspicious_matches}"
    )
    print(
        "Auffällige Wechselgruppen:   "
        f"{unpaired_groups}"
    )
    print(
        "Unvollständige Event-Zeilen: "
        f"{incomplete_events}"
    )

    print()

    if suspicious_matches == 0:
        print(
            "ERGEBNIS: Alle gespeicherten "
            "Wechsel sind paarweise vollständig."
        )
    else:
        print(
            "ERGEBNIS: Auffällige Wechsel "
            "gefunden. Die Blöcke oben zeigen "
            "exakt, welche IN/OUT-Seite fehlt."
        )

    connection.close()


if __name__ == "__main__":
    main()