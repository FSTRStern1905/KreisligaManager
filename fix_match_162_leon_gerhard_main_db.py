from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

BACKUP_DIR = Path(
    "data/database/backups"
)

MATCH_ID = 162

SOURCE_PLAYER_ID = 584
TARGET_PLAYER_ID = 436

EXPECTED_SOURCE_NAME = (
    "Leon",
    "Gerhard",
)

EXPECTED_TARGET_NAME = (
    "Leon",
    "Gerhard",
)

EXPECTED_HISTORICAL_TEAM_ID = 2
EXPECTED_TEAM_MINUTES = 990


def create_backup() -> Path:
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / (
            "kreisligamanager_before_"
            "leon_gerhard_584_to_436_"
            f"{timestamp}.db"
        )
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    return backup_path


def get_player(
    connection: sqlite3.Connection,
    player_id: int,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            player_id,
            team_id,
            first_name,
            last_name,
            external_id
        FROM players
        WHERE player_id = ?
        """,
        (player_id,),
    ).fetchone()


def get_aliases(
    connection: sqlite3.Connection,
    player_id: int,
) -> list[str]:
    return [
        str(row["external_id"])
        for row in connection.execute(
            """
            SELECT external_id
            FROM player_external_ids
            WHERE player_id = ?
            ORDER BY external_id
            """,
            (player_id,),
        ).fetchall()
    ]


def get_lineup_team_ids(
    connection: sqlite3.Connection,
    player_id: int,
) -> list[int]:
    return [
        int(row["team_id"])
        for row in connection.execute(
            """
            SELECT DISTINCT team_id
            FROM lineups
            WHERE
                match_id = ?
                AND player_id = ?
            ORDER BY team_id
            """,
            (
                MATCH_ID,
                player_id,
            ),
        ).fetchall()
    ]


def get_event_team_ids(
    connection: sqlite3.Connection,
    player_id: int,
) -> list[int]:
    rows = connection.execute(
        """
        SELECT DISTINCT team_id
        FROM events
        WHERE
            match_id = ?
            AND (
                player_id = ?
                OR related_player_id = ?
            )
            AND team_id IS NOT NULL
        ORDER BY team_id
        """,
        (
            MATCH_ID,
            player_id,
            player_id,
        ),
    ).fetchall()

    return [
        int(row["team_id"])
        for row in rows
    ]


def get_team_minutes(
    connection: sqlite3.Connection,
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
        ORDER BY pms.team_id
        """,
        (MATCH_ID,),
    ).fetchall()


def get_target_match_stat(
    connection: sqlite3.Connection,
) -> sqlite3.Row | None:
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
        INNER JOIN players AS p
            ON p.player_id = pms.player_id
        WHERE
            pms.match_id = ?
            AND pms.player_id = ?
        """,
        (
            MATCH_ID,
            TARGET_PLAYER_ID,
        ),
    ).fetchone()


def validate_identity(
    connection: sqlite3.Connection,
) -> tuple[
    sqlite3.Row,
    sqlite3.Row,
]:
    source = get_player(
        connection,
        SOURCE_PLAYER_ID,
    )

    target = get_player(
        connection,
        TARGET_PLAYER_ID,
    )

    if source is None:
        raise RuntimeError(
            "Quellspieler 584 fehlt."
        )

    if target is None:
        raise RuntimeError(
            "Zielspieler 436 fehlt."
        )

    source_name = (
        (source["first_name"] or "").strip(),
        (source["last_name"] or "").strip(),
    )

    target_name = (
        (target["first_name"] or "").strip(),
        (target["last_name"] or "").strip(),
    )

    if source_name != EXPECTED_SOURCE_NAME:
        raise RuntimeError(
            f"Unerwarteter Quellspieler: "
            f"{source_name}"
        )

    if target_name != EXPECTED_TARGET_NAME:
        raise RuntimeError(
            f"Unerwarteter Zielspieler: "
            f"{target_name}"
        )

    source_event_teams = get_event_team_ids(
        connection,
        SOURCE_PLAYER_ID,
    )

    target_lineup_teams = get_lineup_team_ids(
        connection,
        TARGET_PLAYER_ID,
    )

    if source_event_teams != [
        EXPECTED_HISTORICAL_TEAM_ID
    ]:
        raise RuntimeError(
            "Quellspieler 584 ist in Spiel 162 "
            "nicht eindeutig team_id=2 zugeordnet."
        )

    if target_lineup_teams != [
        EXPECTED_HISTORICAL_TEAM_ID
    ]:
        raise RuntimeError(
            "Zielspieler 436 steht in Spiel 162 "
            "nicht eindeutig für team_id=2 im Lineup."
        )

    return (
        source,
        target,
    )


def print_team_minutes(
    title: str,
    rows: list[sqlite3.Row],
) -> None:
    print()
    print(title)
    print("-" * 110)

    for row in rows:
        print(dict(row))


def main() -> None:
    print("=" * 110)
    print(
        "HAUPT-DB FIX: "
        "LEON GERHARD 584 -> 436"
    )
    print("=" * 110)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {DB_PATH}"
        )

    backup_path = create_backup()

    print(f"Haupt-DB: {DB_PATH}")
    print(f"Backup:   {backup_path}")
    print(
        "Es wird ausschließlich die bestätigte "
        "Leon-Gerhard-Dublette zusammengeführt "
        "und Spiel 162 neu berechnet."
    )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        repository = PlayerRepository(
            connection
        )

        source, target = validate_identity(
            connection
        )

        print()
        print("VOR FIX")
        print("-" * 110)
        print(
            "Quelle:",
            dict(source),
        )
        print(
            "Ziel:  ",
            dict(target),
        )

        source_aliases = set(
            get_aliases(
                connection,
                SOURCE_PLAYER_ID,
            )
        )

        target_aliases = set(
            get_aliases(
                connection,
                TARGET_PLAYER_ID,
            )
        )

        print(
            "Quell-Aliase:",
            sorted(source_aliases),
        )
        print(
            "Ziel-Aliase: ",
            sorted(target_aliases),
        )

        print_team_minutes(
            "TEAM-MINUTEN VORHER",
            get_team_minutes(
                connection
            ),
        )

        target_team_id = target[
            "team_id"
        ]

        if target_team_id is None:
            raise RuntimeError(
                "Zielspieler 436 besitzt keine "
                "aktuelle team_id."
            )

        print()
        print("TEMPORÄRE MERGE-NORMALISIERUNG")
        print("-" * 110)
        print(
            f"source.team_id "
            f"{source['team_id']} -> "
            f"{target_team_id}"
        )
        print(
            "Diese Änderung dient ausschließlich "
            "dem Repository-Sicherheitscheck; "
            "der Quellspieler wird direkt danach "
            "gelöscht."
        )

        connection.execute(
            """
            UPDATE players
            SET team_id = ?
            WHERE player_id = ?
            """,
            (
                int(target_team_id),
                SOURCE_PLAYER_ID,
            ),
        )
        connection.commit()

        result_id = repository.merge_players(
            source_player_id=SOURCE_PLAYER_ID,
            target_player_id=TARGET_PLAYER_ID,
            commit=True,
        )

        if result_id != TARGET_PLAYER_ID:
            raise RuntimeError(
                "Repository gab eine unerwartete "
                "Ziel-ID zurück."
            )

        if get_player(
            connection,
            SOURCE_PLAYER_ID,
        ) is not None:
            raise RuntimeError(
                "Quellspieler 584 wurde "
                "nicht entfernt."
            )

        merged_aliases = set(
            get_aliases(
                connection,
                TARGET_PLAYER_ID,
            )
        )

        expected_aliases = (
            source_aliases
            | target_aliases
        )

        missing_aliases = (
            expected_aliases
            - merged_aliases
        )

        if missing_aliases:
            raise RuntimeError(
                "Nach Merge fehlen Aliase: "
                + ", ".join(
                    sorted(
                        missing_aliases
                    )
                )
            )

        builder = PlayerMatchStatsBuilder(
            connection
        )

        result = builder.build(
            MATCH_ID
        )

        print()
        print("BUILDERERGEBNIS")
        print("-" * 110)
        print(result)

        target_stat = (
            get_target_match_stat(
                connection
            )
        )

        if target_stat is None:
            raise RuntimeError(
                "Leon-Gerhard-Statistik "
                "für Spiel 162 fehlt."
            )

        print()
        print("LEON GERHARD NACH REBUILD")
        print("-" * 110)
        print(
            dict(target_stat)
        )

        if int(
            target_stat["is_starting"]
        ) != 1:
            raise RuntimeError(
                "Leon Gerhard ist nicht "
                "mehr Starter."
            )

        if int(
            target_stat[
                "was_substituted_out"
            ]
        ) != 1:
            raise RuntimeError(
                "54'-Auswechslung fehlt."
            )

        if int(
            target_stat["minute_out"]
        ) != 54:
            raise RuntimeError(
                "minute_out ist nicht 54."
            )

        if int(
            target_stat[
                "minutes_played"
            ]
        ) != 54:
            raise RuntimeError(
                "minutes_played ist nicht 54."
            )

        team_minutes = get_team_minutes(
            connection
        )

        print_team_minutes(
            "TEAM-MINUTEN NACH FIX",
            team_minutes,
        )

        djk = next(
            (
                row
                for row in team_minutes
                if int(row["team_id"])
                == EXPECTED_HISTORICAL_TEAM_ID
            ),
            None,
        )

        if djk is None:
            raise RuntimeError(
                "DJK-Teamzeile fehlt."
            )

        if int(
            djk["team_minutes"]
        ) != EXPECTED_TEAM_MINUTES:
            raise RuntimeError(
                "DJK St. Matthias Trier "
                "landet nicht bei 990 Minuten."
            )

        connection.commit()

        print()
        print("=" * 110)
        print(
            "ERGEBNIS: HAUPT-DB FIX ERFOLGREICH."
        )
        print(
            "Leon Gerhard 584 wurde in 436 "
            "zusammengeführt."
        )
        print(
            "Spiel 162 wurde neu berechnet "
            "und DJK St. Matthias Trier "
            "liegt bei 990 Minuten."
        )
        print("=" * 110)

    except Exception:
        connection.rollback()
        print()
        print(
            "FEHLER: Fix wurde abgebrochen."
        )
        print(
            "Backup bleibt erhalten:"
        )
        print(
            backup_path
        )
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
