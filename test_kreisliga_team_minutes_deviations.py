from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(
    "data/database/player_match_stats_builder_interval_test.db"
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
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id,
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


def load_team_stats(
    connection: sqlite3.Connection,
    match_id: int,
    team_id: int,
) -> list[sqlite3.Row]:
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


def classify_case(
    events: list[sqlite3.Row],
) -> tuple[str, str]:
    if not events:
        return (
            "B",
            "Keine Wechsel-Events vorhanden, aber Team-Minuten weichen ab.",
        )

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
                f"{len(zero_or_missing)} Wechsel-Events mit "
                "Minute 0/NULL."
            ),
        )

    return (
        "B",
        "Alle Wechselminuten vorhanden, Team-Minuten trotzdem != 990.",
    )


def player_name(
    first_name: str | None,
    last_name: str | None,
    player_id: int,
) -> str:
    name = (
        f"{first_name or ''} "
        f"{last_name or ''}"
    ).strip()

    return name or f"player_id={player_id}"


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
            "KREISLIGA A7: SAMMELDIAGNOSE "
            "TEAM-MINUTEN != 990"
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

        group_a: list[
            tuple[sqlite3.Row, str]
        ] = []

        group_b: list[
            tuple[sqlite3.Row, str]
        ] = []

        for row in rows:
            events = load_team_sub_events(
                connection,
                int(row["match_id"]),
                int(row["team_id"]),
            )

            group, reason = classify_case(
                events
            )

            if group == "A":
                group_a.append(
                    (
                        row,
                        reason,
                    )
                )
            else:
                group_b.append(
                    (
                        row,
                        reason,
                    )
                )

        print()
        print("=" * 100)
        print(
            "GRUPPE A - QUELLSEITIG UNBEKANNTE "
            "WECHSELMINUTEN"
        )
        print("=" * 100)

        if not group_a:
            print("(keine)")
        else:
            for row, reason in group_a:
                print()
                print(
                    f"Spiel {row['match_id']} | "
                    f"ST {row['matchday']} | "
                    f"{row['home_team']} - "
                    f"{row['away_team']}"
                )
                print(
                    f"Team:    {row['team_name']}"
                )
                print(
                    f"Minuten: {row['team_minutes']}"
                )
                print(
                    f"Grund:   {reason}"
                )

                events = load_team_sub_events(
                    connection,
                    int(row["match_id"]),
                    int(row["team_id"]),
                )

                for event in events:
                    print(
                        f"  {event['minute']}' "
                        f"{event['code']:<18} "
                        f"{player_name(event['first_name'], event['last_name'], int(event['player_id']))}"
                        f" ↔ "
                        f"{player_name(event['related_first_name'], event['related_last_name'], int(event['related_player_id'])) if event['related_player_id'] is not None else '?'}"
                    )

        print()
        print("=" * 100)
        print(
            "GRUPPE B - ECHTE RECHENABWEICHUNG "
            "TROTZ VOLLSTÄNDIGER WECHSELMINUTEN"
        )
        print("=" * 100)

        if not group_b:
            print("(keine)")
        else:
            for row, reason in group_b:
                print()
                print(
                    f"Spiel {row['match_id']} | "
                    f"ST {row['matchday']} | "
                    f"{row['home_team']} - "
                    f"{row['away_team']}"
                )
                print(
                    f"Team:    {row['team_name']}"
                )
                print(
                    f"Minuten: {row['team_minutes']}"
                )
                print(
                    f"Grund:   {reason}"
                )

                print("SPIELERSTATS")
                print("-" * 100)

                stats = load_team_stats(
                    connection,
                    int(row["match_id"]),
                    int(row["team_id"]),
                )

                for stat in stats:
                    print(
                        f"  {player_name(stat['first_name'], stat['last_name'], int(stat['player_id'])):<30} "
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
                        f"{player_name(event['first_name'], event['last_name'], int(event['player_id']))}"
                        f" ↔ "
                        f"{player_name(event['related_first_name'], event['related_last_name'], int(event['related_player_id'])) if event['related_player_id'] is not None else '?'}"
                    )

        print()
        print("=" * 100)
        print("GESAMTERGEBNIS")
        print("=" * 100)
        print(
            f"Gruppe A - Quelle unvollständig: "
            f"{len(group_a)}"
        )
        print(
            f"Gruppe B - echte Rechenfehler:    "
            f"{len(group_b)}"
        )

        if not group_b:
            print()
            print(
                "STATUS: OK - keine echten "
                "Rechenabweichungen gefunden."
            )
        else:
            print()
            print(
                "STATUS: PRÜFEN - echte "
                "Rechenabweichungen vorhanden."
            )

        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
