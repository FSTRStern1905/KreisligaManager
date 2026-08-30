from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")

EXPECTED_TEAM_MINUTES = 990
EXPECTED_STARTERS = 11


def player_name(
    first_name: str | None,
    last_name: str | None,
    player_id: int,
) -> str:
    name = " ".join(
        part.strip()
        for part in (
            first_name or "",
            last_name or "",
        )
        if part and part.strip()
    )

    return name or f"player_id={player_id}"


def load_competitions(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            competition_id,
            name
        FROM competitions
        ORDER BY competition_id
        """
    ).fetchall()


def load_team_rows(
    connection: sqlite3.Connection,
    competition_id: int,
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

            COUNT(*) AS squad_size,

            SUM(
                CASE
                    WHEN pms.is_starting = 1
                    THEN 1
                    ELSE 0
                END
            ) AS starters,

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

            SUM(pms.minutes_played) AS team_minutes,

            SUM(
                CASE
                    WHEN pms.minutes_played < 0
                    THEN 1
                    ELSE 0
                END
            ) AS negative_minutes,

            SUM(
                CASE
                    WHEN pms.minutes_played > 90
                    THEN 1
                    ELSE 0
                END
            ) AS over_90_minutes,

            SUM(
                CASE
                    WHEN pms.is_starting = 1
                         AND COALESCE(pms.minute_in, -1) != 0
                    THEN 1
                    ELSE 0
                END
            ) AS starter_bad_minute_in,

            SUM(
                CASE
                    WHEN pms.is_starting = 0
                         AND pms.was_substituted_in = 0
                         AND pms.minutes_played > 0
                    THEN 1
                    ELSE 0
                END
            ) AS bench_minutes_without_sub_in,

            SUM(
                CASE
                    WHEN pms.minute_in IS NOT NULL
                         AND pms.minute_out IS NOT NULL
                         AND pms.minute_out < pms.minute_in
                    THEN 1
                    ELSE 0
                END
            ) AS invalid_minute_order

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
            AND m.detail_imported = 1

        GROUP BY
            pms.match_id,
            pms.team_id,
            t.name,
            m.matchday,
            ht.name,
            at.name

        ORDER BY
            pms.match_id,
            pms.team_id
        """,
        (competition_id,),
    ).fetchall()


def load_event_counts(
    connection: sqlite3.Connection,
    competition_id: int,
) -> dict[tuple[int, int], dict[str, int]]:
    rows = connection.execute(
        """
        SELECT
            e.match_id,
            e.team_id,
            et.code,
            COUNT(*) AS count_events
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        INNER JOIN matches AS m
            ON m.match_id = e.match_id
        WHERE
            m.competition_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
            AND e.team_id IS NOT NULL
        GROUP BY
            e.match_id,
            e.team_id,
            et.code
        """,
        (competition_id,),
    ).fetchall()

    result: dict[
        tuple[int, int],
        dict[str, int],
    ] = defaultdict(
        lambda: {
            "in": 0,
            "out": 0,
        }
    )

    for row in rows:
        key = (
            int(row["match_id"]),
            int(row["team_id"]),
        )

        direction = (
            "in"
            if row["code"] == "SUBSTITUTION_IN"
            else "out"
        )

        result[key][direction] = int(
            row["count_events"] or 0
        )

    return result


def load_player_problems(
    connection: sqlite3.Connection,
    competition_id: int,
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
            pms.is_starting,
            pms.was_substituted_in,
            pms.was_substituted_out,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played

        FROM player_match_stats AS pms

        INNER JOIN matches AS m
            ON m.match_id = pms.match_id

        INNER JOIN players AS p
            ON p.player_id = pms.player_id

        WHERE
            m.competition_id = ?
            AND m.detail_imported = 1
            AND (
                pms.minutes_played < 0
                OR pms.minutes_played > 90
                OR (
                    pms.minute_in IS NOT NULL
                    AND pms.minute_in < 0
                )
                OR (
                    pms.minute_out IS NOT NULL
                    AND pms.minute_out < 0
                )
                OR (
                    pms.minute_in IS NOT NULL
                    AND pms.minute_out IS NOT NULL
                    AND pms.minute_out < pms.minute_in
                )
                OR (
                    pms.is_starting = 1
                    AND COALESCE(pms.minute_in, -1) != 0
                )
                OR (
                    pms.is_starting = 0
                    AND pms.was_substituted_in = 0
                    AND pms.minutes_played > 0
                )
            )

        ORDER BY
            pms.match_id,
            pms.team_id,
            pms.player_id
        """,
        (competition_id,),
    ).fetchall()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        competitions = load_competitions(
            connection
        )

        print("=" * 92)
        print("EINSATZMINUTEN-DIAGNOSE PRO WETTBEWERB")
        print("=" * 92)

        for competition in competitions:
            competition_id = int(
                competition["competition_id"]
            )
            competition_name = str(
                competition["name"]
            )

            team_rows = load_team_rows(
                connection,
                competition_id,
            )

            event_counts = load_event_counts(
                connection,
                competition_id,
            )

            player_problems = load_player_problems(
                connection,
                competition_id,
            )

            technical_rows: list[
                tuple[sqlite3.Row, str]
            ] = []

            source_rows: list[
                tuple[sqlite3.Row, str]
            ] = []

            exact_team_minutes = 0

            for row in team_rows:
                match_id = int(
                    row["match_id"]
                )
                team_id = int(
                    row["team_id"]
                )

                events = event_counts[
                    (match_id, team_id)
                ]

                team_minutes = int(
                    row["team_minutes"] or 0
                )
                starters = int(
                    row["starters"] or 0
                )

                if (
                    team_minutes
                    == EXPECTED_TEAM_MINUTES
                ):
                    exact_team_minutes += 1

                hard_error = (
                    starters != EXPECTED_STARTERS
                    or int(
                        row["negative_minutes"] or 0
                    ) > 0
                    or int(
                        row["over_90_minutes"] or 0
                    ) > 0
                    or int(
                        row[
                            "starter_bad_minute_in"
                        ]
                        or 0
                    ) > 0
                    or int(
                        row[
                            "bench_minutes_without_sub_in"
                        ]
                        or 0
                    ) > 0
                    or int(
                        row[
                            "invalid_minute_order"
                        ]
                        or 0
                    ) > 0
                )

                if hard_error:
                    technical_rows.append(
                        (
                            row,
                            "struktureller Minutenfehler",
                        )
                    )
                    continue

                if (
                    team_minutes
                    != EXPECTED_TEAM_MINUTES
                ):
                    if events["in"] != events["out"]:
                        source_rows.append(
                            (
                                row,
                                (
                                    "quellseitig einseitiger "
                                    "Wechsel"
                                ),
                            )
                        )
                    else:
                        technical_rows.append(
                            (
                                row,
                                (
                                    "Mannschaftsminuten "
                                    "abweichend trotz "
                                    "ausgeglichenen Wechseln"
                                ),
                            )
                        )

            print()
            print("=" * 92)
            print(
                f"{competition_name} "
                f"(competition_id={competition_id})"
            )
            print("=" * 92)

            print(
                "Spiel/Team-Kombinationen geprüft: "
                f"{len(team_rows)}"
            )
            print(
                "Exakt 990 Mannschaftsminuten:      "
                f"{exact_team_minutes}/{len(team_rows)}"
            )
            print(
                "Quellseitige Abweichungen:         "
                f"{len(source_rows)}"
            )
            print(
                "Technische Minutenfehler:          "
                f"{len(technical_rows)}"
            )
            print(
                "Ungültige Spielerzeilen:           "
                f"{len(player_problems)}"
            )

            if source_rows:
                print()
                print(
                    "QUELLSEITIGE MINUTENABWEICHUNGEN "
                    "(KEIN IMPORTFEHLER)"
                )
                print("-" * 92)

                for row, reason in source_rows[:30]:
                    key = (
                        int(row["match_id"]),
                        int(row["team_id"]),
                    )
                    events = event_counts[key]

                    print(
                        f"Spiel {row['match_id']} | "
                        f"ST {row['matchday']} | "
                        f"{row['home_team']} - "
                        f"{row['away_team']} | "
                        f"{row['team_name']} | "
                        f"Minuten={row['team_minutes']} | "
                        f"IN/OUT="
                        f"{events['in']}/{events['out']} | "
                        f"{reason}"
                    )

            if technical_rows:
                print()
                print("TECHNISCHE AUFFÄLLIGKEITEN")
                print("-" * 92)

                for row, reason in technical_rows[:30]:
                    key = (
                        int(row["match_id"]),
                        int(row["team_id"]),
                    )
                    events = event_counts[key]

                    print(
                        f"Spiel {row['match_id']} | "
                        f"ST {row['matchday']} | "
                        f"{row['home_team']} - "
                        f"{row['away_team']} | "
                        f"{row['team_name']} | "
                        f"Starter={row['starters']} | "
                        f"Minuten={row['team_minutes']} | "
                        f"IN/OUT="
                        f"{events['in']}/{events['out']} | "
                        f"{reason}"
                    )

            if player_problems:
                print()
                print(
                    "UNGÜLTIGE SPIELER-MINUTENZEILEN"
                )
                print("-" * 92)

                for row in player_problems[:30]:
                    print(
                        f"Spiel {row['match_id']} | "
                        f"{player_name(row['first_name'], row['last_name'], int(row['player_id']))} | "
                        f"Starter={row['is_starting']} | "
                        f"IN={row['was_substituted_in']} | "
                        f"OUT={row['was_substituted_out']} | "
                        f"minute_in={row['minute_in']} | "
                        f"minute_out={row['minute_out']} | "
                        f"minutes={row['minutes_played']}"
                    )

            print()

            if (
                not technical_rows
                and not player_problems
            ):
                if source_rows:
                    print(
                        "STATUS: OK - Einsatzminuten "
                        "technisch sauber; nur "
                        "quellseitige Lücken vorhanden."
                    )
                else:
                    print(
                        "STATUS: OK - Einsatzminuten "
                        "vollständig sauber."
                    )
            else:
                print(
                    "STATUS: PRÜFEN - technische "
                    "Minutenfehler vorhanden."
                )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
