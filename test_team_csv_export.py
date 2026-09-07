from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.team_csv_export_service import (
    TeamCsvExportService,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


def select_competition(
    connection: sqlite3.Connection,
) -> int:
    rows = connection.execute(
        """
        SELECT
            c.competition_id,
            c.name AS competition_name,
            s.name AS season_name,
            COUNT(ct.team_id) AS team_count
        FROM competitions AS c
        INNER JOIN seasons AS s
            ON s.season_id = c.season_id
        LEFT JOIN competition_teams AS ct
            ON ct.competition_id = c.competition_id
        GROUP BY
            c.competition_id,
            c.name,
            s.name
        ORDER BY
            s.name DESC,
            c.name
        """
    ).fetchall()

    if not rows:
        raise RuntimeError(
            "Keine Wettbewerbe vorhanden."
        )

    print()
    print("=" * 78)
    print("WETTBEWERB AUSWÄHLEN")
    print("=" * 78)

    for index, row in enumerate(
        rows,
        start=1,
    ):
        print(
            f"[{index:>2}] "
            f"{row['competition_name']} "
            f"| {row['season_name']} "
            f"| {row['team_count']} Teams"
        )

    while True:
        value = input(
            "\nNummer: "
        ).strip()

        try:
            selected_index = int(value) - 1

            if (
                0
                <= selected_index
                < len(rows)
            ):
                return int(
                    rows[
                        selected_index
                    ]["competition_id"]
                )

        except ValueError:
            pass

        print(
            "Ungültige Auswahl."
        )


def select_team(
    connection: sqlite3.Connection,
    competition_id: int,
) -> int:
    rows = connection.execute(
        """
        SELECT
            t.team_id,
            t.name AS team_name
        FROM competition_teams AS ct
        INNER JOIN teams AS t
            ON t.team_id = ct.team_id
        WHERE
            ct.competition_id = ?
        ORDER BY
            t.name
        """,
        (competition_id,),
    ).fetchall()

    if not rows:
        raise RuntimeError(
            "Keine Mannschaften im Wettbewerb."
        )

    print()
    print("=" * 78)
    print("MANNSCHAFT AUSWÄHLEN")
    print("=" * 78)

    for index, row in enumerate(
        rows,
        start=1,
    ):
        print(
            f"[{index:>2}] "
            f"{row['team_name']}"
        )

    while True:
        value = input(
            "\nNummer: "
        ).strip()

        try:
            selected_index = int(value) - 1

            if (
                0
                <= selected_index
                < len(rows)
            ):
                return int(
                    rows[
                        selected_index
                    ]["team_id"]
                )

        except ValueError:
            pass

        print(
            "Ungültige Auswahl."
        )


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: "
            f"{DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    try:
        competition_id = (
            select_competition(
                connection
            )
        )

        team_id = select_team(
            connection=connection,
            competition_id=competition_id,
        )

        print()
        print("=" * 78)
        print("CSV-EXPORT")
        print("=" * 78)

        exporter = TeamCsvExportService(
            connection
        )

        output_path = exporter.export_team(
            competition_id=competition_id,
            team_id=team_id,
        )

        print()
        print(
            "Export erfolgreich."
        )
        print(
            f"Ordner: {output_path}"
        )

        files = sorted(
            output_path.glob(
                "*.csv"
            )
        )

        print()
        print(
            f"CSV-Dateien: {len(files)}"
        )
        print("-" * 78)

        for file_path in files:
            size_kb = (
                file_path.stat().st_size
                / 1024
            )

            print(
                f"{file_path.name:<30} "
                f"{size_kb:>8.1f} KB"
            )

        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()