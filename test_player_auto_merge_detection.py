from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.database.repositories.player_repository import PlayerRepository


SOURCE_DB = Path("data/database/alias_fix_test.db")
TEST_DB = Path("data/database/auto_merge_detection_test.db")


def normalize(value: str | None) -> str:
    return " ".join((value or "").strip().casefold().split())


def main() -> None:
    print("=" * 90)
    print("AUTOMERGE-KANDIDATEN: SICHERHEITSTEST")
    print("=" * 90)

    shutil.copy2(SOURCE_DB, TEST_DB)

    connection = sqlite3.connect(TEST_DB)
    connection.row_factory = sqlite3.Row
    repository = PlayerRepository(connection)

    try:
        # Simuliert den jetzt korrekt dekodierten Lineup-Datensatz.
        external_id = "01MH0AKR74000001VV0AG13EVSFDFGE6"
        first_name = "Kevin"
        last_name = "Stöger"
        team_id = 21

        external_player = repository.get_by_external_id(external_id)

        if external_player is None:
            raise RuntimeError("External-ID-Spieler nicht gefunden.")

        candidates = connection.execute(
            """
            SELECT
                player_id,
                first_name,
                last_name,
                team_id,
                external_id
            FROM players
            WHERE
                player_id <> ?
                AND team_id = ?
            ORDER BY player_id
            """,
            (
                external_player["player_id"],
                team_id,
            ),
        ).fetchall()

        exact = [
            row
            for row in candidates
            if normalize(row["first_name"]) == normalize(first_name)
            and normalize(row["last_name"]) == normalize(last_name)
        ]

        print("External-ID-Spieler:")
        print(dict(external_player))
        print()
        print("Vollständiger Parsername:")
        print(f"{first_name} {last_name}")
        print()
        print(f"Eindeutige exakte Kandidaten im selben Team: {len(exact)}")

        for row in exact:
            print(dict(row))

        if len(exact) != 1:
            print()
            print("ERGEBNIS: KEIN AUTOMERGE.")
            return

        target = exact[0]

        print()
        print(
            f"MERGE-KANDIDAT EINDEUTIG: "
            f"{external_player['player_id']} -> {target['player_id']}"
        )

        repository.merge_players(
            source_player_id=external_player["player_id"],
            target_player_id=target["player_id"],
            commit=True,
        )

        resolved = repository.get_by_external_id(external_id)

        print()
        print("NACH MERGE:")
        print(dict(resolved) if resolved else None)

        ok = (
            resolved is not None
            and resolved["player_id"] == target["player_id"]
            and normalize(resolved["first_name"]) == normalize(first_name)
            and normalize(resolved["last_name"]) == normalize(last_name)
        )

        print()
        print("=" * 90)
        print(
            "ERGEBNIS: AUTOMERGE-LOGIK SAUBER."
            if ok
            else "ERGEBNIS: AUTOMERGE-LOGIK FEHLERHAFT."
        )
        print("=" * 90)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
