from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.services.player_match_stats.player_match_stats_builder import (
    PlayerMatchStatsBuilder,
)


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)

BACKUP_DIR = Path(
    "data/backups"
)


def create_backup() -> Path:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = BACKUP_DIR / (
        "kreisligamanager_before_"
        f"player_match_stats_rebuild_"
        f"{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    return backup_path


def main() -> None:
    backup_path = create_backup()

    print("=" * 78)
    print("PLAYER_MATCH_STATS REBUILD")
    print("=" * 78)
    print(
        f"Backup erstellt: {backup_path}"
    )
    print(
        f"Datenbank:        {DB_PATH}"
    )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        builder = PlayerMatchStatsBuilder(
            connection
        )

        matches = connection.execute(
            """
            SELECT
                m.match_id,
                m.matchday,
                m.competition_id,
                c.name AS competition_name,
                ht.name AS home_team,
                at.name AS away_team
            FROM matches AS m
            INNER JOIN competitions AS c
                ON c.competition_id =
                   m.competition_id
            INNER JOIN teams AS ht
                ON ht.team_id =
                   m.home_team_id
            INNER JOIN teams AS at
                ON at.team_id =
                   m.away_team_id
            WHERE
                m.detail_imported = 1
            ORDER BY
                m.competition_id,
                m.matchday,
                m.match_id
            """
        ).fetchall()

        print()
        print(
            f"Detailspiele gefunden: "
            f"{len(matches)}"
        )
        print()

        rebuilt = 0
        failed = 0
        seeded = 0
        stats_created = 0

        current_competition: str | None = None

        for index, match in enumerate(
            matches,
            start=1,
        ):
            competition_name = str(
                match["competition_name"]
            )

            if (
                competition_name
                != current_competition
            ):
                current_competition = (
                    competition_name
                )

                print()
                print("-" * 78)
                print(
                    f"Wettbewerb: "
                    f"{competition_name}"
                )
                print("-" * 78)

            match_id = int(
                match["match_id"]
            )

            print(
                f"[{index}/{len(matches)}] "
                f"Spiel {match_id} | "
                f"ST {match['matchday']} | "
                f"{match['home_team']} - "
                f"{match['away_team']}"
            )

            try:
                result = builder.build(
                    match_id
                )

                rebuilt += 1
                seeded += int(
                    result.get(
                        "event_seed_stats_created",
                        0,
                    )
                    or 0
                )
                stats_created += int(
                    result.get(
                        "stats_created",
                        0,
                    )
                    or 0
                )

            except Exception as exc:
                failed += 1

                print(
                    f"  FEHLER: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        print()
        print("=" * 78)
        print("ZUSAMMENFASSUNG")
        print("=" * 78)
        print(
            f"Spiele erfolgreich neu gebaut: "
            f"{rebuilt}"
        )
        print(
            f"Spiele fehlgeschlagen:          "
            f"{failed}"
        )
        print(
            f"Zusätzliche Stats aus Events:   "
            f"{seeded}"
        )
        print(
            f"Stats-Zeilen geschrieben:       "
            f"{stats_created}"
        )
        print()
        print(
            f"Backup: {backup_path}"
        )

        if failed == 0:
            print()
            print(
                "ERGEBNIS: REBUILD ERFOLGREICH."
            )
        else:
            print()
            print(
                "ERGEBNIS: REBUILD MIT FEHLERN."
            )
            print(
                "Bei Bedarf kann die Datenbank "
                "aus dem Backup wiederhergestellt "
                "werden."
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
