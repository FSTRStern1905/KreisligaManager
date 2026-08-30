from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path(
    "data/database/player_match_stats_builder_current_test.db"
)

COMPETITION_ID = 1
EXPECTED_TEAM_MINUTES = 990


def load_team_rows(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.match_id,
            pms.team_id,
            t.name AS team_name,
            m.matchday,
            ht.name AS home_team,
            at.name AS away_team,
            SUM(pms.minutes_played) AS team_minutes,
            SUM(pms.is_starting) AS starters
        FROM player_match_stats AS pms

        INNER JOIN matches AS m
            ON m.match_id = pms.match_id

        INNER JOIN teams AS t
            ON t.team_id = pms.team_id

        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id

        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id

        WHERE
            m.competition_id = ?

        GROUP BY
            pms.match_id,
            pms.team_id,
            t.name,
            m.matchday,
            ht.name,
            at.name

        HAVING
            SUM(pms.minutes_played) != ?

        ORDER BY
            pms.match_id,
            pms.team_id
        """,
        (
            COMPETITION_ID,
            EXPECTED_TEAM_MINUTES,
        ),
    ).fetchall()


def load_team_sub_events(
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
            e.value,
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


def load_team_dismissals(
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
            e.player_id,
            p.first_name,
            p.last_name
        FROM events AS e

        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id

        LEFT JOIN players AS p
            ON p.player_id = e.player_id

        WHERE
            e.match_id = ?
            AND e.team_id = ?
            AND et.code IN (
                'RED_CARD',
                'YELLOW_RED_CARD'
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


def load_team_stats(
    connection: sqlite3.Connection,
    match_id: int,
    team_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
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
            AND pms.team_id = ?

        ORDER BY
            pms.is_starting DESC,
            pms.player_id
        """,
        (
            match_id,
            team_id,
        ),
    ).fetchall()


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


def has_impossible_substitution_sequence(
    events: list[sqlite3.Row],
) -> tuple[bool, str]:
    """
    Erkennt quellseitig widersprüchliche Wechselketten.

    Beispiel:
        Spieler IN 71'
        Spieler IN 86'
        ohne OUT dazwischen

    Ein legitimer Rückwechsel sieht dagegen so aus:
        IN -> OUT -> IN

    Die Erkennung arbeitet nur mit direkten player_id-Events.
    """
    by_player: dict[
        int,
        list[sqlite3.Row],
    ] = defaultdict(list)

    for row in events:
        player_id = row["player_id"]

        if player_id is None:
            continue

        by_player[
            int(player_id)
        ].append(row)

    problems: list[str] = []

    for player_id, rows in by_player.items():
        active = False
        seen_in = False

        for row in rows:
            code = str(
                row["code"]
            ).strip().upper()

            minute = row["minute"]

            if code == "SUBSTITUTION_IN":
                if active:
                    name = player_name(
                        row["first_name"],
                        row["last_name"],
                        player_id,
                    )

                    problems.append(
                        f"{name}: erneutes IN in "
                        f"{minute}' ohne OUT dazwischen"
                    )

                active = True
                seen_in = True

            elif code == "SUBSTITUTION_OUT":
                if seen_in:
                    active = False

    if not problems:
        return (
            False,
            "",
        )

    return (
        True,
        "; ".join(
            problems
        ),
    )


def classify_case(
    events: list[sqlite3.Row],
    dismissals: list[sqlite3.Row],
    team_minutes: int,
) -> tuple[str, str]:
    zero_or_missing = [
        row
        for row in events
        if row["minute"] is None
        or int(row["minute"]) <= 0
    ]

    if zero_or_missing:
        return (
            "A",
            (
                f"{len(zero_or_missing)} Wechsel-Events "
                "mit Minute 0/NULL."
            ),
        )

    impossible, reason = (
        has_impossible_substitution_sequence(
            events
        )
    )

    if impossible:
        return (
            "E",
            (
                "Quellseitig widersprüchliche "
                f"Wechselkette: {reason}"
            ),
        )

    if (
        dismissals
        and team_minutes
        < EXPECTED_TEAM_MINUTES
    ):
        return (
            "C",
            (
                "Abweichung durch Platzverweis "
                "(kein Rechenfehler)."
            ),
        )

    max_sub_minute = max(
        (
            int(row["minute"])
            for row in events
            if row["minute"] is not None
        ),
        default=0,
    )

    if max_sub_minute > 90:
        return (
            "D",
            (
                "Wechsel in der Nachspielzeit "
                "(>90') vorhanden."
            ),
        )

    return (
        "B",
        (
            "Alle Wechselminuten vorhanden, "
            "Abweichung bleibt technisch zu prüfen."
        ),
    )


def print_group_b_details(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
) -> None:
    print("SPIELERSTATS")
    print("-" * 100)

    stats = load_team_stats(
        connection,
        int(row["match_id"]),
        int(row["team_id"]),
    )

    for stat in stats:
        print(
            f"  "
            f"{player_name(stat['first_name'], stat['last_name'], int(stat['player_id'])):<30} "
            f"Starter={stat['is_starting']} "
            f"IN={stat['was_substituted_in']} "
            f"OUT={stat['was_substituted_out']} "
            f"minute_in={stat['minute_in']} "
            f"minute_out={stat['minute_out']} "
            f"minutes={stat['minutes_played']}"
        )

    print("WECHSEL")
    print("-" * 100)

    events = load_team_sub_events(
        connection,
        int(row["match_id"]),
        int(row["team_id"]),
    )

    for event in events:
        print(
            f"  {event['minute']}' "
            f"{event['code']:<18} "
            f"{player_name(event['first_name'], event['last_name'], event['player_id'])}"
            f" ↔ "
            f"{player_name(event['related_first_name'], event['related_last_name'], event['related_player_id'])}"
            f" | {event['value'] or ''}"
        )


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
        rows = load_team_rows(
            connection
        )

        print("=" * 100)
        print(
            "FINALER KREISLIGA-A7-"
            "MINUTEN-QUALITÄTSTEST"
        )
        print("=" * 100)
        print(f"Datenbank: {DB_PATH}")
        print(
            "Haupt-DB wird NICHT verändert."
        )
        print(
            f"Abweichende Spiel/Team-Fälle: "
            f"{len(rows)}"
        )

        groups: dict[
            str,
            list[tuple[sqlite3.Row, str]],
        ] = {
            "A": [],
            "B": [],
            "C": [],
            "D": [],
            "E": [],
        }

        for row in rows:
            events = load_team_sub_events(
                connection,
                int(row["match_id"]),
                int(row["team_id"]),
            )

            dismissals = load_team_dismissals(
                connection,
                int(row["match_id"]),
                int(row["team_id"]),
            )

            group, reason = classify_case(
                events,
                dismissals,
                int(
                    row["team_minutes"]
                    or 0
                ),
            )

            groups[group].append(
                (
                    row,
                    reason,
                )
            )

        titles = {
            "A": (
                "GRUPPE A - QUELLSEITIG UNBEKANNTE "
                "WECHSELMINUTEN"
            ),
            "B": (
                "GRUPPE B - ECHTE TECHNISCHE "
                "RECHENABWEICHUNG"
            ),
            "C": (
                "GRUPPE C - PLATZVERWEIS "
                "(ERKLÄRTE ABWEICHUNG)"
            ),
            "D": (
                "GRUPPE D - NACHSPIELZEIT "
                "(ERKLÄRTE ABWEICHUNG)"
            ),
            "E": (
                "GRUPPE E - QUELLSEITIG "
                "WIDERSPRÜCHLICHE WECHSELKETTE"
            ),
        }

        for group in (
            "A",
            "B",
            "C",
            "D",
            "E",
        ):
            print()
            print("=" * 100)
            print(
                titles[group]
            )
            print("=" * 100)

            group_rows = groups[
                group
            ]

            if not group_rows:
                print("(keine)")
                continue

            for row, reason in group_rows:
                print()
                print(
                    f"Spiel {row['match_id']} | "
                    f"ST {row['matchday']} | "
                    f"{row['home_team']} - "
                    f"{row['away_team']}"
                )
                print(
                    f"Team:    "
                    f"{row['team_name']}"
                )
                print(
                    f"Minuten: "
                    f"{row['team_minutes']}"
                )
                print(
                    f"Grund:   {reason}"
                )

                if group == "B":
                    print_group_b_details(
                        connection,
                        row,
                    )

                if group == "E":
                    events = load_team_sub_events(
                        connection,
                        int(row["match_id"]),
                        int(row["team_id"]),
                    )

                    print("WECHSEL")
                    print("-" * 100)

                    for event in events:
                        print(
                            f"  {event['minute']}' "
                            f"{event['code']:<18} "
                            f"{player_name(event['first_name'], event['last_name'], event['player_id'])}"
                            f" ↔ "
                            f"{player_name(event['related_first_name'], event['related_last_name'], event['related_player_id'])}"
                            f" | {event['value'] or ''}"
                        )

        print()
        print("=" * 100)
        print("GESAMTERGEBNIS")
        print("=" * 100)
        print(
            f"Gruppe A - Quelle Minute unbekannt: "
            f"{len(groups['A'])}"
        )
        print(
            f"Gruppe B - echte Rechenfehler:      "
            f"{len(groups['B'])}"
        )
        print(
            f"Gruppe C - Platzverweis:            "
            f"{len(groups['C'])}"
        )
        print(
            f"Gruppe D - Nachspielzeit:           "
            f"{len(groups['D'])}"
        )
        print(
            f"Gruppe E - Quelle widersprüchlich:  "
            f"{len(groups['E'])}"
        )

        print()

        if not groups["B"]:
            print(
                "STATUS: OK - keine echten "
                "technischen Minutenfehler."
            )
            print(
                "Verbleibende Abweichungen sind "
                "quellseitig oder durch reguläre "
                "Sonderfälle erklärt."
            )
        else:
            print(
                "STATUS: PRÜFEN - echte "
                "technische Minutenfehler vorhanden."
            )

        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
