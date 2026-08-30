from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)


SOURCE_DB = Path(
    "data/database/backups/"
    "kreisligamanager_before_return_substitution_stats_fix_"
    "20260830_130856.db"
)

TEST_DB = Path(
    "data/database/"
    "player_match_stats_builder_interval_test.db"
)

COMPETITION_ID = 1

CHECK_MATCH_IDS = (
    14,
    21,
    41,
    47,
    50,
    54,
    73,
    76,
    94,
    98,
    109,
    122,
    139,
    141,
    148,
    157,
    161,
    165,
    181,
)


def get_match_label(
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


def get_team_minute_rows(
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
            SUM(pms.minutes_played) AS team_minutes
        FROM player_match_stats AS pms
        INNER JOIN teams AS t
            ON t.team_id = pms.team_id
        WHERE pms.match_id = ?
        GROUP BY
            pms.team_id,
            t.name
        ORDER BY
            pms.team_id
        """,
        (match_id,),
    ).fetchall()


def get_bad_player_rows(
    connection: sqlite3.Connection,
    match_id: int,
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
            AND (
                pms.minutes_played < 0
                OR pms.minutes_played > 90
                OR (
                    pms.is_starting = 1
                    AND COALESCE(pms.minute_in, -1) != 0
                )
                OR (
                    pms.is_starting = 0
                    AND pms.was_substituted_in = 0
                    AND pms.minutes_played > 0
                )
                OR (
                    pms.minute_in IS NOT NULL
                    AND pms.minute_out IS NOT NULL
                    AND pms.minute_out < pms.minute_in
                )
            )
        ORDER BY
            pms.team_id,
            pms.player_id
        """,
        (match_id,),
    ).fetchall()


def get_suspicious_zero_zero_rows(
    connection: sqlite3.Connection,
    match_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
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
            AND pms.is_starting = 0
            AND pms.minute_in = 0
            AND pms.minute_out = 0
            AND pms.minutes_played > 0
        ORDER BY
            pms.team_id,
            pms.player_id
        """,
        (match_id,),
    ).fetchall()


def player_name(
    row: sqlite3.Row,
) -> str:
    name = (
        f"{row['first_name'] or ''} "
        f"{row['last_name'] or ''}"
    ).strip()

    return name or f"player_id={row['player_id']}"


def main() -> None:
    print("=" * 100)
    print(
        "FULL-PIPELINE TEST: "
        "PLAYER_MATCH_STATS BUILDER + RÜCK-/MEHRFACHWECHSEL"
    )
    print("=" * 100)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Backup nicht gefunden: {SOURCE_DB}"
        )

    shutil.copy2(
        SOURCE_DB,
        TEST_DB,
    )

    print(f"Quelle:  {SOURCE_DB}")
    print(f"Test-DB: {TEST_DB}")
    print(
        "Haupt-DB wird NICHT verändert."
    )

    connection = sqlite3.connect(
        TEST_DB
    )
    connection.row_factory = sqlite3.Row

    try:
        builder = PlayerMatchStatsBuilder(
            connection
        )

        total_bad_rows = 0
        total_zero_zero = 0
        minute_deviation_rows = 0

        for match_id in CHECK_MATCH_IDS:
            print()
            print("=" * 100)
            print(
                get_match_label(
                    connection,
                    match_id,
                )
            )
            print("=" * 100)

            result = builder.build(
                match_id
            )

            print(
                "Builder: "
                f"lineups={result.get('lineups_found')} | "
                f"events={result.get('events_found')} | "
                f"stats={result.get('stats_created')}"
            )

            team_rows = get_team_minute_rows(
                connection,
                match_id,
            )

            for row in team_rows:
                team_minutes = int(
                    row["team_minutes"] or 0
                )

                marker = (
                    "OK"
                    if team_minutes == 990
                    else "PRÜFEN"
                )

                if team_minutes != 990:
                    minute_deviation_rows += 1

                print(
                    f"[{marker}] "
                    f"{row['team_name']} | "
                    f"Starter={row['starters']} | "
                    f"Kader={row['squad_size']} | "
                    f"Minuten={team_minutes}"
                )

            bad_rows = get_bad_player_rows(
                connection,
                match_id,
            )

            zero_zero_rows = (
                get_suspicious_zero_zero_rows(
                    connection,
                    match_id,
                )
            )

            total_bad_rows += len(
                bad_rows
            )
            total_zero_zero += len(
                zero_zero_rows
            )

            if bad_rows:
                print()
                print("UNGÜLTIGE SPIELERZEILEN")
                print("-" * 100)

                for row in bad_rows:
                    print(
                        f"{player_name(row)} | "
                        f"Starter={row['is_starting']} | "
                        f"IN={row['was_substituted_in']} | "
                        f"OUT={row['was_substituted_out']} | "
                        f"minute_in={row['minute_in']} | "
                        f"minute_out={row['minute_out']} | "
                        f"minutes={row['minutes_played']}"
                    )

            if zero_zero_rows:
                print()
                print(
                    "VERDÄCHTIG: BANKSPIELER "
                    "0'->0' MIT POSITIVEN MINUTEN"
                )
                print("-" * 100)

                for row in zero_zero_rows:
                    print(
                        f"{player_name(row)} | "
                        f"IN={row['was_substituted_in']} | "
                        f"OUT={row['was_substituted_out']} | "
                        f"minutes={row['minutes_played']}"
                    )

        print()
        print("=" * 100)
        print("GESAMTERGEBNIS")
        print("=" * 100)
        print(
            f"Geprüfte Spiele:              "
            f"{len(CHECK_MATCH_IDS)}"
        )
        print(
            f"Ungültige Spielerzeilen:      "
            f"{total_bad_rows}"
        )
        print(
            f"Verdächtige 0'->0'-Bankfälle: "
            f"{total_zero_zero}"
        )
        print(
            f"Team-Minuten ≠ 990:           "
            f"{minute_deviation_rows}"
        )

        if (
            total_bad_rows == 0
            and total_zero_zero == 0
        ):
            print()
            print(
                "ERGEBNIS: FULL-PIPELINE "
                "SPIELERLOGIK SAUBER."
            )
            print(
                "Abweichende Team-Minuten "
                "werden separat bewertet."
            )
            print("=" * 100)
            return

        print()
        print(
            "ERGEBNIS: FULL-PIPELINE "
            "NOCH NICHT SAUBER."
        )
        print("=" * 100)

        raise RuntimeError(
            "PlayerMatchStatsBuilder-"
            "Qualitätsprüfung nicht bestanden."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
