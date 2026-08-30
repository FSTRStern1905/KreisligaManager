from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path

from src.services.player_match_stats.event_mapper import (
    EventMapper,
)
from src.services.player_match_stats.lineup_mapper import (
    LineupMapper,
)


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

COMPETITION_ID = 1
REGULATION_MINUTES = 90


def load_lineups(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT
            match_id,
            team_id,
            player_id,
            is_starting,
            shirt_number,
            position
        FROM lineups
        WHERE match_id = ?
        ORDER BY
            team_id,
            is_starting DESC,
            player_id
        """,
        (match_id,),
    ).fetchall()

    return [
        {
            "match_id": int(row["match_id"]),
            "team_id": int(row["team_id"]),
            "player_id": int(row["player_id"]),
            "is_starting": bool(row["is_starting"]),
            "shirt_number": row["shirt_number"],
            "position": row["position"] or "",
        }
        for row in rows
    ]


def load_events(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT
            e.event_id,
            e.match_id,
            e.team_id,
            e.player_id,
            e.related_player_id,
            e.minute,
            et.code AS event_type_code
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        WHERE e.match_id = ?
        ORDER BY
            e.minute,
            e.event_id
        """,
        (match_id,),
    ).fetchall()

    return [
        {
            "event_id": int(row["event_id"]),
            "match_id": int(row["match_id"]),
            "team_id": (
                int(row["team_id"])
                if row["team_id"] is not None
                else None
            ),
            "player_id": (
                int(row["player_id"])
                if row["player_id"] is not None
                else None
            ),
            "related_player_id": (
                int(row["related_player_id"])
                if row["related_player_id"] is not None
                else None
            ),
            "minute": (
                int(row["minute"])
                if row["minute"] is not None
                else None
            ),
            "event_type_code": str(
                row["event_type_code"]
            ),
        }
        for row in rows
    ]


def player_name(
    connection: sqlite3.Connection,
    player_id: int,
) -> str:
    row = connection.execute(
        """
        SELECT
            first_name,
            last_name
        FROM players
        WHERE player_id = ?
        """,
        (player_id,),
    ).fetchone()

    if row is None:
        return f"player_id={player_id}"

    return (
        f"{row['first_name'] or ''} "
        f"{row['last_name'] or ''}"
    ).strip() or f"player_id={player_id}"


def match_name(
    connection: sqlite3.Connection,
    match_id: int,
) -> str:
    row = connection.execute(
        """
        SELECT
            m.matchday,
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
        return f"Spiel {match_id}"

    return (
        f"Spiel {match_id} | "
        f"ST {row['matchday']} | "
        f"{row['home_team']} - "
        f"{row['away_team']}"
    )


def find_return_substitution_cases(
    connection: sqlite3.Connection,
) -> list[tuple[int, int]]:
    rows = connection.execute(
        """
        SELECT DISTINCT
            l.match_id,
            l.player_id
        FROM lineups AS l

        INNER JOIN matches AS m
            ON m.match_id = l.match_id

        WHERE
            m.competition_id = ?
            AND m.detail_imported = 1
            AND l.is_starting = 1

            AND EXISTS (
                SELECT 1
                FROM events AS e_out
                INNER JOIN event_types AS et_out
                    ON et_out.event_type_id =
                        e_out.event_type_id
                WHERE
                    e_out.match_id = l.match_id
                    AND e_out.player_id = l.player_id
                    AND et_out.code =
                        'SUBSTITUTION_OUT'
            )

            AND EXISTS (
                SELECT 1
                FROM events AS e_in
                INNER JOIN event_types AS et_in
                    ON et_in.event_type_id =
                        e_in.event_type_id
                WHERE
                    e_in.match_id = l.match_id
                    AND e_in.player_id = l.player_id
                    AND et_in.code =
                        'SUBSTITUTION_IN'
            )

        ORDER BY
            l.match_id,
            l.player_id
        """,
        (COMPETITION_ID,),
    ).fetchall()

    return [
        (
            int(row["match_id"]),
            int(row["player_id"]),
        )
        for row in rows
    ]


def normalize_minute(
    value: int | None,
) -> int:
    if value is None:
        return 0

    return max(
        0,
        min(
            int(value),
            REGULATION_MINUTES,
        ),
    )


def reference_minutes_for_player(
    *,
    is_starting: bool,
    player_id: int,
    events: list[dict],
) -> dict:
    relevant = [
        event
        for event in events
        if event.get("player_id") == player_id
        and str(
            event.get(
                "event_type_code",
                "",
            )
        ).upper()
        in {
            "SUBSTITUTION_IN",
            "SUBSTITUTION_OUT",
            "RED_CARD",
            "YELLOW_RED_CARD",
        }
    ]

    priority = {
        "SUBSTITUTION_OUT": 0,
        "RED_CARD": 1,
        "YELLOW_RED_CARD": 1,
        "SUBSTITUTION_IN": 2,
    }

    relevant.sort(
        key=lambda event: (
            normalize_minute(
                event.get("minute")
            ),
            priority.get(
                str(
                    event.get(
                        "event_type_code",
                        "",
                    )
                ).upper(),
                9,
            ),
            int(
                event.get("event_id") or 0
            ),
        )
    )

    active = is_starting
    current_start = (
        0
        if is_starting
        else None
    )

    minutes_played = 0
    first_in = None
    first_out = None

    was_in = False
    was_out = False
    sent_off = False

    for event in relevant:
        code = str(
            event["event_type_code"]
        ).upper()

        minute = normalize_minute(
            event.get("minute")
        )

        if code == "SUBSTITUTION_OUT":
            was_out = True

            if first_out is None:
                first_out = minute

            if (
                active
                and current_start is not None
            ):
                minutes_played += max(
                    0,
                    minute - current_start,
                )

            active = False
            current_start = None
            continue

        if code == "SUBSTITUTION_IN":
            was_in = True

            if first_in is None:
                first_in = minute

            if sent_off:
                continue

            if not active:
                active = True
                current_start = minute

            continue

        if code in {
            "RED_CARD",
            "YELLOW_RED_CARD",
        }:
            if first_out is None:
                first_out = minute

            if (
                active
                and current_start is not None
            ):
                minutes_played += max(
                    0,
                    minute - current_start,
                )

            active = False
            current_start = None
            sent_off = True

    if (
        active
        and current_start is not None
    ):
        minutes_played += max(
            0,
            REGULATION_MINUTES
            - current_start,
        )

    return {
        "minute_in": (
            0
            if is_starting
            else first_in
        ),
        "minute_out": (
            first_out
            if first_out is not None
            else (
                REGULATION_MINUTES
                if is_starting
                or first_in is not None
                else None
            )
        ),
        "minutes_played": minutes_played,
        "was_substituted_in": was_in,
        "was_substituted_out": was_out,
    }


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank fehlt: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        cases = find_return_substitution_cases(
            connection
        )

        print("=" * 100)
        print(
            "RÜCKWECHSEL-SAMMELTEST / EVENTMAPPER"
        )
        print("=" * 100)
        print(f"Datenbank: {DB_PATH}")
        print(
            "Haupt-DB wird NICHT verändert."
        )
        print(
            f"Gefundene Rückwechsel-Fälle: "
            f"{len(cases)}"
        )

        if not cases:
            raise RuntimeError(
                "Keine Rückwechsel-Fälle gefunden."
            )

        cases_by_match: dict[
            int,
            list[int],
        ] = defaultdict(list)

        for match_id, player_id in cases:
            cases_by_match[
                match_id
            ].append(
                player_id
            )

        passed = 0
        failed = 0

        for match_id in sorted(
            cases_by_match
        ):
            lineups = load_lineups(
                connection,
                match_id,
            )
            events = load_events(
                connection,
                match_id,
            )

            stats = LineupMapper().build(
                lineups
            )

            EventMapper().apply(
                stats,
                events,
            )

            stats_by_player = {
                int(stat.player_id): stat
                for stat in stats
            }

            print()
            print("=" * 100)
            print(
                match_name(
                    connection,
                    match_id,
                )
            )
            print("=" * 100)

            for player_id in cases_by_match[
                match_id
            ]:
                stat = stats_by_player.get(
                    player_id
                )

                if stat is None:
                    failed += 1
                    print(
                        f"[FEHLER] "
                        f"{player_name(connection, player_id)} "
                        "- keine berechnete Statistik."
                    )
                    continue

                expected = (
                    reference_minutes_for_player(
                        is_starting=True,
                        player_id=player_id,
                        events=events,
                    )
                )

                actual = {
                    "minute_in": stat.minute_in,
                    "minute_out": stat.minute_out,
                    "minutes_played": (
                        stat.minutes_played
                    ),
                    "was_substituted_in": bool(
                        stat.was_substituted_in
                    ),
                    "was_substituted_out": bool(
                        stat.was_substituted_out
                    ),
                }

                problems: list[str] = []

                for key in expected:
                    if (
                        actual[key]
                        != expected[key]
                    ):
                        problems.append(
                            f"{key}: "
                            f"IST={actual[key]} "
                            f"SOLL={expected[key]}"
                        )

                if stat.minute_in != 0:
                    problems.append(
                        "Starter hat minute_in != 0"
                    )

                if not stat.was_substituted_in:
                    problems.append(
                        "Rückwechsel ohne "
                        "was_substituted_in"
                    )

                if not stat.was_substituted_out:
                    problems.append(
                        "Rückwechsel ohne "
                        "was_substituted_out"
                    )

                name = player_name(
                    connection,
                    player_id,
                )

                if problems:
                    failed += 1
                    print(
                        f"[FEHLER] {name}"
                    )
                    print(
                        f"  IST:  {actual}"
                    )
                    print(
                        f"  SOLL: {expected}"
                    )

                    for problem in problems:
                        print(
                            f"  - {problem}"
                        )
                else:
                    passed += 1
                    print(
                        f"[OK] {name} | "
                        f"Minuten={actual['minutes_played']} | "
                        f"minute_in={actual['minute_in']} | "
                        f"minute_out={actual['minute_out']}"
                    )

        print()
        print("=" * 100)
        print("GESAMTERGEBNIS")
        print("=" * 100)
        print(
            f"Bestanden: {passed}"
        )
        print(
            f"Fehler:    {failed}"
        )
        print(
            f"Gesamt:    {passed + failed}"
        )

        if failed:
            print()
            print(
                "ERGEBNIS: RÜCKWECHSEL-LOGIK "
                "NOCH NICHT SAUBER."
            )
            print("=" * 100)

            raise RuntimeError(
                "Rückwechsel-Sammeltest "
                "nicht bestanden."
            )

        print()
        print(
            "ERGEBNIS: ALLE RÜCKWECHSEL "
            "WERDEN KORREKT BERECHNET."
        )
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
