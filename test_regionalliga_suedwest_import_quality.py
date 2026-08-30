from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)

COMPETITION_NAME = "Regionalliga Südwest"


def get_competition(
    connection: sqlite3.Connection,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            competition_id,
            name
        FROM competitions
        WHERE name = ?
        ORDER BY competition_id DESC
        LIMIT 1
        """,
        (COMPETITION_NAME,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Wettbewerb nicht gefunden: {COMPETITION_NAME}"
        )

    return row


def get_matches(
    connection: sqlite3.Connection,
    competition_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            m.match_id,
            m.matchday,
            m.external_id,
            m.status,
            m.detail_imported,
            m.home_goals,
            m.away_goals,
            m.attendance,
            ht.name AS home_team,
            at.name AS away_team
        FROM matches AS m
        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id
        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id
        WHERE m.competition_id = ?
        ORDER BY
            m.matchday,
            m.match_id
        """,
        (competition_id,),
    ).fetchall()


def load_counts(
    connection: sqlite3.Connection,
    competition_id: int,
) -> dict[int, dict]:
    result: dict[int, dict] = defaultdict(
        lambda: {
            "lineups": 0,
            "events": 0,
            "stats": 0,
            "starters": 0,
        }
    )

    for row in connection.execute(
        """
        SELECT
            l.match_id,
            COUNT(*) AS cnt,
            SUM(
                CASE
                    WHEN l.is_starting = 1
                    THEN 1
                    ELSE 0
                END
            ) AS starters
        FROM lineups AS l
        INNER JOIN matches AS m
            ON m.match_id = l.match_id
        WHERE m.competition_id = ?
        GROUP BY l.match_id
        """,
        (competition_id,),
    ).fetchall():
        match_id = int(
            row["match_id"]
        )

        result[match_id]["lineups"] = int(
            row["cnt"] or 0
        )
        result[match_id]["starters"] = int(
            row["starters"] or 0
        )

    for row in connection.execute(
        """
        SELECT
            e.match_id,
            COUNT(*) AS cnt
        FROM events AS e
        INNER JOIN matches AS m
            ON m.match_id = e.match_id
        WHERE m.competition_id = ?
        GROUP BY e.match_id
        """,
        (competition_id,),
    ).fetchall():
        match_id = int(
            row["match_id"]
        )

        result[match_id]["events"] = int(
            row["cnt"] or 0
        )

    for row in connection.execute(
        """
        SELECT
            pms.match_id,
            COUNT(*) AS cnt
        FROM player_match_stats AS pms
        INNER JOIN matches AS m
            ON m.match_id = pms.match_id
        WHERE m.competition_id = ?
        GROUP BY pms.match_id
        """,
        (competition_id,),
    ).fetchall():
        match_id = int(
            row["match_id"]
        )

        result[match_id]["stats"] = int(
            row["cnt"] or 0
        )

    return result


def load_event_type_counts(
    connection: sqlite3.Connection,
    match_id: int,
) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT
            et.code,
            COUNT(*) AS cnt
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        WHERE e.match_id = ?
        GROUP BY et.code
        ORDER BY et.code
        """,
        (match_id,),
    ).fetchall()

    return {
        str(row["code"]): int(
            row["cnt"] or 0
        )
        for row in rows
    }


def get_stat_team_summary(
    connection: sqlite3.Connection,
    match_id: int,
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
            SUM(
                COALESCE(
                    pms.minutes_played,
                    0
                )
            ) AS team_minutes
        FROM player_match_stats AS pms
        INNER JOIN teams AS t
            ON t.team_id = pms.team_id
        WHERE pms.match_id = ?
        GROUP BY
            pms.team_id,
            t.name
        ORDER BY pms.team_id
        """,
        (match_id,),
    ).fetchall()


def print_match_line(
    row: sqlite3.Row,
    counts: dict,
) -> None:
    attendance = (
        row["attendance"]
        if row["attendance"] is not None
        else "-"
    )

    print(
        f"Spiel {row['match_id']} | "
        f"ST {row['matchday']} | "
        f"{row['home_team']} - "
        f"{row['away_team']} | "
        f"Lineups={counts['lineups']} | "
        f"Starter={counts['starters']} | "
        f"Events={counts['events']} | "
        f"Stats={counts['stats']} | "
        f"Zuschauer={attendance}"
    )


def main() -> None:
    print("=" * 110)
    print(
        "REGIONALLIGA SÜDWEST 2025/26 "
        "- FINALER QUALITÄTSTEST"
    )
    print("=" * 110)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Test-DB nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        competition = get_competition(
            connection
        )

        competition_id = int(
            competition["competition_id"]
        )

        matches = get_matches(
            connection,
            competition_id,
        )

        counts_by_match = load_counts(
            connection,
            competition_id,
        )

        print(f"Datenbank: {DB_PATH}")
        print(
            f"Wettbewerb: "
            f"{competition['name']} "
            f"(competition_id={competition_id})"
        )
        print(
            "Haupt-DB wird NICHT verändert."
        )
        print(
            f"Spiele geprüft: {len(matches)}"
        )

        missing_details: list[
            tuple[sqlite3.Row, dict]
        ] = []
        missing_lineups: list[
            tuple[sqlite3.Row, dict]
        ] = []
        invalid_starters: list[
            tuple[sqlite3.Row, dict]
        ] = []
        missing_events: list[
            tuple[sqlite3.Row, dict]
        ] = []
        missing_stats: list[
            tuple[sqlite3.Row, dict]
        ] = []
        missing_attendance: list[
            tuple[sqlite3.Row, dict]
        ] = []
        event_goal_mismatches: list[
            tuple[
                sqlite3.Row,
                dict,
                dict[str, int],
            ]
        ] = []
        stat_minute_cases: list[
            tuple[
                sqlite3.Row,
                sqlite3.Row,
            ]
        ] = []

        for match in matches:
            match_id = int(
                match["match_id"]
            )

            counts = counts_by_match[
                match_id
            ]

            if int(
                match["detail_imported"]
                or 0
            ) != 1:
                missing_details.append(
                    (
                        match,
                        counts,
                    )
                )

            if counts["lineups"] == 0:
                missing_lineups.append(
                    (
                        match,
                        counts,
                    )
                )

            if (
                counts["lineups"] > 0
                and counts["starters"] != 22
            ):
                invalid_starters.append(
                    (
                        match,
                        counts,
                    )
                )

            if counts["events"] == 0:
                missing_events.append(
                    (
                        match,
                        counts,
                    )
                )

            if counts["stats"] == 0:
                missing_stats.append(
                    (
                        match,
                        counts,
                    )
                )

            if match["attendance"] is None:
                missing_attendance.append(
                    (
                        match,
                        counts,
                    )
                )

            if counts["events"] > 0:
                event_counts = (
                    load_event_type_counts(
                        connection,
                        match_id,
                    )
                )

                event_goals = (
                    event_counts.get(
                        "GOAL",
                        0,
                    )
                    + event_counts.get(
                        "OWN_GOAL",
                        0,
                    )
                    + event_counts.get(
                        "PENALTY_GOAL",
                        0,
                    )
                )

                score_goals = int(
                    match["home_goals"]
                    or 0
                ) + int(
                    match["away_goals"]
                    or 0
                )

                if event_goals != score_goals:
                    event_goal_mismatches.append(
                        (
                            match,
                            counts,
                            event_counts,
                        )
                    )

            if counts["stats"] > 0:
                team_rows = (
                    get_stat_team_summary(
                        connection,
                        match_id,
                    )
                )

                for team_row in team_rows:
                    starters = int(
                        team_row["starters"]
                        or 0
                    )

                    team_minutes = int(
                        team_row["team_minutes"]
                        or 0
                    )

                    if (
                        starters != 11
                        or team_minutes != 990
                    ):
                        stat_minute_cases.append(
                            (
                                match,
                                team_row,
                            )
                        )

        print()
        print("=" * 110)
        print("ÜBERSICHT")
        print("=" * 110)
        print(
            f"Detailimport fehlt:       "
            f"{len(missing_details)}"
        )
        print(
            f"Lineup fehlt:             "
            f"{len(missing_lineups)}"
        )
        print(
            f"Startelf ≠ 22 gesamt:     "
            f"{len(invalid_starters)}"
        )
        print(
            f"Events fehlen komplett:   "
            f"{len(missing_events)}"
        )
        print(
            f"Player-Stats fehlen:      "
            f"{len(missing_stats)}"
        )
        print(
            f"Zuschauer fehlt:          "
            f"{len(missing_attendance)}"
        )
        print(
            f"Tore ≠ Goal-Events:       "
            f"{len(event_goal_mismatches)}"
        )
        print(
            f"Team-Minuten/Starter Fall:"
            f" {len(stat_minute_cases)}"
        )

        print()
        print("=" * 110)
        print(
            "SPIELE OHNE EVENTS "
            "(WAHRSCHEINLICH QUELLSEITIG)"
        )
        print("=" * 110)

        if not missing_events:
            print("(keine)")
        else:
            for match, counts in (
                missing_events
            ):
                print_match_line(
                    match,
                    counts,
                )

        print()
        print("=" * 110)
        print(
            "SPIELE OHNE PLAYER-STATS"
        )
        print("=" * 110)

        if not missing_stats:
            print("(keine)")
        else:
            for match, counts in (
                missing_stats
            ):
                print_match_line(
                    match,
                    counts,
                )

        print()
        print("=" * 110)
        print(
            "SPIELE OHNE ZUSCHAUERZAHL"
        )
        print("=" * 110)

        if not missing_attendance:
            print("(keine)")
        else:
            for match, counts in (
                missing_attendance
            ):
                print_match_line(
                    match,
                    counts,
                )

        print()
        print("=" * 110)
        print(
            "TOR/EVENT-ABWEICHUNGEN"
        )
        print("=" * 110)

        if not event_goal_mismatches:
            print("(keine)")
        else:
            for (
                match,
                counts,
                event_counts,
            ) in event_goal_mismatches:
                print_match_line(
                    match,
                    counts,
                )

                score_goals = int(
                    match["home_goals"]
                    or 0
                ) + int(
                    match["away_goals"]
                    or 0
                )

                event_goals = (
                    event_counts.get(
                        "GOAL",
                        0,
                    )
                    + event_counts.get(
                        "OWN_GOAL",
                        0,
                    )
                    + event_counts.get(
                        "PENALTY_GOAL",
                        0,
                    )
                )

                print(
                    f"  Ergebnis-Tore={score_goals} | "
                    f"Event-Tore={event_goals} | "
                    f"Eventtypen={event_counts}"
                )

        print()
        print("=" * 110)
        print(
            "PLAYER-STATS / TEAM-MINUTEN "
            "AUFFÄLLIG"
        )
        print("=" * 110)

        if not stat_minute_cases:
            print("(keine)")
        else:
            for (
                match,
                team_row,
            ) in stat_minute_cases:
                print(
                    f"Spiel {match['match_id']} | "
                    f"ST {match['matchday']} | "
                    f"{match['home_team']} - "
                    f"{match['away_team']} | "
                    f"Team={team_row['team_name']} | "
                    f"Starter={team_row['starters']} | "
                    f"Kader={team_row['squad_size']} | "
                    f"Minuten={team_row['team_minutes']}"
                )

        print()
        print("=" * 110)
        print("GESAMTERGEBNIS")
        print("=" * 110)

        structural_ok = (
            not missing_details
            and not missing_lineups
            and not invalid_starters
        )

        technical_ok = (
            structural_ok
            and not missing_stats
        )

        if structural_ok:
            print(
                "STRUKTUR: OK - alle 306 Spiele "
                "detailimportiert und mit Aufstellung."
            )
        else:
            print(
                "STRUKTUR: PRÜFEN."
            )

        if technical_ok:
            print(
                "PLAYER-STATS: OK - jedes Spiel "
                "besitzt Player-Stats."
            )
        else:
            print(
                "PLAYER-STATS: PRÜFEN - "
                f"{len(missing_stats)} Spiele ohne Stats."
            )

        print(
            f"EVENT-ABDECKUNG: "
            f"{len(matches) - len(missing_events)}"
            f"/{len(matches)}"
        )
        print(
            f"ZUSCHAUER-ABDECKUNG: "
            f"{len(matches) - len(missing_attendance)}"
            f"/{len(matches)}"
        )

        print()
        print(
            "Hinweis: Fehlende Events oder Zuschauer "
            "können quellseitig korrekt sein und werden "
            "separat bewertet."
        )

        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
