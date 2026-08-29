from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        competitions = connection.execute(
            """
            SELECT
                competition_id,
                name
            FROM competitions
            ORDER BY competition_id
            """
        ).fetchall()

        print("=" * 88)
        print("WECHSEL-DIAGNOSE PRO WETTBEWERB")
        print("=" * 88)

        for competition in competitions:
            competition_id = int(
                competition["competition_id"]
            )
            competition_name = str(
                competition["name"]
            )

            print()
            print("=" * 88)
            print(
                f"{competition_name} "
                f"(competition_id={competition_id})"
            )
            print("=" * 88)

            event_rows = connection.execute(
                """
                SELECT
                    e.match_id,
                    e.team_id,
                    et.code AS event_type,
                    COUNT(*) AS event_count,
                    SUM(
                        CASE
                            WHEN e.player_id IS NULL
                            THEN 1
                            ELSE 0
                        END
                    ) AS without_player,
                    SUM(
                        CASE
                            WHEN e.related_player_id IS NULL
                            THEN 1
                            ELSE 0
                        END
                    ) AS without_related_player
                FROM events AS e
                INNER JOIN event_types AS et
                    ON et.event_type_id =
                       e.event_type_id
                INNER JOIN matches AS m
                    ON m.match_id = e.match_id
                WHERE
                    m.competition_id = ?
                    AND et.code IN (
                        'SUBSTITUTION_IN',
                        'SUBSTITUTION_OUT'
                    )
                GROUP BY
                    e.match_id,
                    e.team_id,
                    et.code
                """,
                (competition_id,),
            ).fetchall()

            stats_rows = connection.execute(
                """
                SELECT
                    pms.match_id,
                    pms.team_id,
                    SUM(
                        CASE
                            WHEN pms.was_substituted_in = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS stats_in,
                    SUM(
                        CASE
                            WHEN pms.was_substituted_out = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS stats_out,
                    SUM(
                        CASE
                            WHEN pms.is_starting = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS starters,
                    COUNT(*) AS squad_size
                FROM player_match_stats AS pms
                INNER JOIN matches AS m
                    ON m.match_id = pms.match_id
                WHERE
                    m.competition_id = ?
                    AND m.detail_imported = 1
                GROUP BY
                    pms.match_id,
                    pms.team_id
                """,
                (competition_id,),
            ).fetchall()

            event_map: dict[
                tuple[int, int],
                dict[str, int],
            ] = defaultdict(
                lambda: {
                    "in": 0,
                    "out": 0,
                    "in_without_player": 0,
                    "out_without_player": 0,
                    "in_without_related": 0,
                    "out_without_related": 0,
                }
            )

            events_without_team = 0
            events_without_team_rows: list[
                sqlite3.Row
            ] = []

            for row in event_rows:
                if row["team_id"] is None:
                    events_without_team += int(
                        row["event_count"] or 0
                    )
                    events_without_team_rows.append(
                        row
                    )
                    continue

                key = (
                    int(row["match_id"]),
                    int(row["team_id"]),
                )

                direction = (
                    "in"
                    if row["event_type"]
                    == "SUBSTITUTION_IN"
                    else "out"
                )

                event_map[key][direction] = int(
                    row["event_count"] or 0
                )
                event_map[key][
                    f"{direction}_without_player"
                ] = int(
                    row["without_player"] or 0
                )
                event_map[key][
                    f"{direction}_without_related"
                ] = int(
                    row["without_related_player"]
                    or 0
                )

            stats_map = {
                (
                    int(row["match_id"]),
                    int(row["team_id"]),
                ): {
                    "in": int(row["stats_in"] or 0),
                    "out": int(row["stats_out"] or 0),
                    "starters": int(
                        row["starters"] or 0
                    ),
                    "squad_size": int(
                        row["squad_size"] or 0
                    ),
                }
                for row in stats_rows
            }

            keys = sorted(
                set(event_map)
                | set(stats_map)
            )

            balanced_events = 0
            source_incomplete = 0
            stats_mismatch = 0
            both_problematic = 0
            starter_problems = 0
            missing_player_refs = 0

            problem_rows: list[
                tuple[str, int, int, dict, dict]
            ] = []

            for key in keys:
                match_id, team_id = key

                events = event_map[key]
                stats = stats_map.get(
                    key,
                    {
                        "in": 0,
                        "out": 0,
                        "starters": 0,
                        "squad_size": 0,
                    },
                )

                events_balanced = (
                    events["in"] == events["out"]
                )

                stats_equal_events = (
                    stats["in"] == events["in"]
                    and stats["out"] == events["out"]
                )

                has_missing_refs = any(
                    events[name] > 0
                    for name in (
                        "in_without_player",
                        "out_without_player",
                    )
                )

                if events_balanced:
                    balanced_events += 1

                if not events_balanced:
                    source_incomplete += 1

                if not stats_equal_events:
                    stats_mismatch += 1

                if (
                    not events_balanced
                    and not stats_equal_events
                ):
                    both_problematic += 1

                if stats["starters"] != 11:
                    starter_problems += 1

                if has_missing_refs:
                    missing_player_refs += 1

                if not events_balanced:
                    classification = (
                        "QUELLE/IMPORT UNVOLLSTÄNDIG"
                    )
                elif not stats_equal_events:
                    classification = (
                        "PLAYER_MATCH_STATS FEHLER"
                    )
                elif stats["starters"] != 11:
                    classification = (
                        "STARTELF AUFFÄLLIG"
                    )
                elif has_missing_refs:
                    classification = (
                        "SPIELERZUORDNUNG FEHLT"
                    )
                else:
                    continue

                problem_rows.append(
                    (
                        classification,
                        match_id,
                        team_id,
                        events,
                        stats,
                    )
                )

            print(
                f"Spiel/Team-Kombinationen geprüft: "
                f"{len(keys)}"
            )
            print(
                f"Event-Wechsel ausgeglichen:       "
                f"{balanced_events}/{len(keys)}"
            )
            print(
                f"Event IN/OUT ungleich:            "
                f"{source_incomplete}"
            )
            print(
                f"Stats ≠ Events:                   "
                f"{stats_mismatch}"
            )
            print(
                f"Davon beide Probleme zugleich:    "
                f"{both_problematic}"
            )
            print(
                f"Startelf ≠ 11:                    "
                f"{starter_problems}"
            )
            print(
                f"Wechsel ohne player_id:           "
                f"{missing_player_refs}"
            )
            print(
                f"Wechsel ohne team_id:             "
                f"{events_without_team}"
            )

            if events_without_team_rows:
                print()
                print("WECHSEL OHNE TEAMZUORDNUNG")
                print("-" * 88)

                for row in events_without_team_rows[:20]:
                    print(
                        f"  Spiel {row['match_id']} | "
                        f"{row['event_type']} | "
                        f"Events={int(row['event_count'] or 0)} | "
                        f"ohne player_id="
                        f"{int(row['without_player'] or 0)}"
                    )

                if len(events_without_team_rows) > 20:
                    print(
                        f"  ... weitere "
                        f"{len(events_without_team_rows) - 20} "
                        f"Gruppen nicht ausgegeben."
                    )

            if not problem_rows:
                print()
                print(
                    "STATUS: OK - keine Auffälligkeiten."
                )
                continue

            print()
            print("ERSTE AUFFÄLLIGKEITEN")
            print("-" * 88)

            for (
                classification,
                match_id,
                team_id,
                events,
                stats,
            ) in problem_rows[:30]:
                match = connection.execute(
                    """
                    SELECT
                        m.matchday,
                        ht.name AS home_team,
                        at.name AS away_team,
                        t.name AS team_name
                    FROM matches AS m
                    INNER JOIN teams AS ht
                        ON ht.team_id =
                           m.home_team_id
                    INNER JOIN teams AS at
                        ON at.team_id =
                           m.away_team_id
                    INNER JOIN teams AS t
                        ON t.team_id = ?
                    WHERE m.match_id = ?
                    """,
                    (
                        team_id,
                        match_id,
                    ),
                ).fetchone()

                if match is None:
                    continue

                print()
                print(
                    f"[{classification}] "
                    f"Spiel {match_id} | "
                    f"ST {match['matchday']} | "
                    f"{match['home_team']} - "
                    f"{match['away_team']}"
                )
                print(
                    f"  Team:   {match['team_name']}"
                )
                print(
                    "  Events: "
                    f"IN={events['in']} "
                    f"OUT={events['out']}"
                )
                print(
                    "  Stats:  "
                    f"IN={stats['in']} "
                    f"OUT={stats['out']} "
                    f"Starter={stats['starters']} "
                    f"Kader={stats['squad_size']}"
                )

                if (
                    events["in_without_player"]
                    or events[
                        "out_without_player"
                    ]
                ):
                    print(
                        "  Ohne player_id: "
                        f"IN="
                        f"{events['in_without_player']} "
                        f"OUT="
                        f"{events['out_without_player']}"
                    )

                details = connection.execute(
                    """
                    SELECT
                        et.code,
                        e.minute,
                        p.first_name,
                        p.last_name,
                        rp.first_name
                            AS related_first_name,
                        rp.last_name
                            AS related_last_name,
                        e.notes
                    FROM events AS e
                    INNER JOIN event_types AS et
                        ON et.event_type_id =
                           e.event_type_id
                    LEFT JOIN players AS p
                        ON p.player_id =
                           e.player_id
                    LEFT JOIN players AS rp
                        ON rp.player_id =
                           e.related_player_id
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

                for detail in details:
                    player = " ".join(
                        part
                        for part in (
                            detail["first_name"]
                            or "",
                            detail["last_name"]
                            or "",
                        )
                        if part
                    ) or "?"

                    related = " ".join(
                        part
                        for part in (
                            detail[
                                "related_first_name"
                            ] or "",
                            detail[
                                "related_last_name"
                            ] or "",
                        )
                        if part
                    ) or "?"

                    print(
                        f"    {detail['minute']!s:>3}' "
                        f"{detail['code']:<18} "
                        f"{player} ↔ {related}"
                    )

            if len(problem_rows) > 30:
                print()
                print(
                    f"... weitere "
                    f"{len(problem_rows) - 30} "
                    f"Auffälligkeiten nicht ausgegeben."
                )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
