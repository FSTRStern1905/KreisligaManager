from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.importer.fussballde.match_event_importer import MatchEventImporter
from src.importer.fussballde.liveticker_data import (
    LivetickerData,
    LivetickerEvent,
)
from src.importer.fussballde.parsers.match_detail_data import MatchDetailData


DB_PATH = Path("data/database/kreisligamanager.db")
JSON_PATH = Path(
    "debug/liveticker/json/"
    "02TKDR1VGS000000VS5489BUVUD1610F.json"
)

MATCH_ID = 260
TARGET_MINUTE = 89


def main() -> None:
    print("=" * 100)
    print("SPIEL 260 TEAM-RESOLVER-DIAGNOSE")
    print("=" * 100)

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    if not JSON_PATH.exists():
        raise FileNotFoundError(JSON_PATH)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        match = connection.execute(
            """
            SELECT
                match_id,
                home_team_id,
                away_team_id
            FROM matches
            WHERE match_id = ?
            """,
            (MATCH_ID,),
        ).fetchone()

        if match is None:
            raise RuntimeError("Spiel 260 nicht gefunden.")

        home_team_id = int(match["home_team_id"])
        away_team_id = int(match["away_team_id"])

        raw = json.load(
            open(
                JSON_PATH,
                encoding="utf-8",
            )
        )

        home_raw = raw.get("home_team") or {}
        away_raw = raw.get("guest_team") or {}

        print()
        print("MATCH")
        print("-" * 100)
        print(f"home_team_id intern: {home_team_id}")
        print(f"away_team_id intern: {away_team_id}")
        print(
            "home external:",
            home_raw.get("id"),
            "|",
            home_raw.get("name"),
        )
        print(
            "away external:",
            away_raw.get("id"),
            "|",
            away_raw.get("name"),
        )

        print()
        print("DB TEAM-EXTERNAL-IDS")
        print("-" * 100)

        for team_id in (
            home_team_id,
            away_team_id,
        ):
            row = connection.execute(
                """
                SELECT
                    team_id,
                    name,
                    external_id
                FROM teams
                WHERE team_id = ?
                """,
                (team_id,),
            ).fetchone()

            print(
                dict(row)
                if row is not None
                else None
            )

        target_raw = None

        for event in raw.get("events", []):
            if (
                event.get("type_id") == 4
                and int(event.get("minute") or 0)
                == TARGET_MINUTE
            ):
                target_raw = event
                break

        if target_raw is None:
            raise RuntimeError(
                "89'-Wechsel nicht gefunden."
            )

        print()
        print("ROH-EVENT")
        print("-" * 100)

        for key in (
            "id",
            "type_id",
            "description",
            "team_id",
            "member_id",
            "member2_id",
            "minute",
        ):
            print(
                f"{key}: {target_raw.get(key)}"
            )

        importer = MatchEventImporter(
            connection
        )

        print()
        print("_resolve_team_by_external_id")
        print("-" * 100)

        direct = importer._resolve_team_by_external_id(
            external_id=str(
                target_raw.get("team_id") or ""
            ),
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )

        print("Ergebnis:", direct)

        print()
        print("DB LOOKUP DER EVENT-TEAM-ID")
        print("-" * 100)

        lookup = connection.execute(
            """
            SELECT
                team_id,
                name,
                external_id
            FROM teams
            WHERE external_id = ?
            """,
            (
                str(
                    target_raw.get("team_id")
                    or ""
                ),
            ),
        ).fetchall()

        if not lookup:
            print("KEIN TREFFER")
        else:
            for row in lookup:
                print(dict(row))

        print()
        print("CACHE-SEED TEST")
        print("-" * 100)

        # Für diesen Test reicht ein minimaler LivetickerData-Aufbau
        # aus den bereits geparsten Strukturen nicht zuverlässig.
        # Deshalb prüfen wir direkt, ob die externe Team-ID überhaupt
        # in der DB auflösbar ist. Genau das entscheidet hier über den
        # direkten Resolver-Pfad.
        cache_key = (
            MATCH_ID,
            importer._normalize_name(
                str(
                    target_raw.get("team_id")
                    or ""
                )
            ),
        )

        print("Cache-Key:", cache_key)
        print(
            "Cache vor Seed:",
            importer._liveticker_team_cache.get(
                cache_key
            ),
        )

        print()
        print("DIAGNOSE")
        print("-" * 100)

        if direct == away_team_id:
            print(
                "Direkter External-ID-Resolver funktioniert."
            )
            print(
                "Dann geht event.team vermutlich bereits vor "
                "_resolve_liveticker_team_id verloren oder enthält "
                "nicht die rohe team_id."
            )
        elif direct is None:
            print(
                "Direkter External-ID-Resolver findet die Liveticker-"
                "Team-ID nicht in teams.external_id."
            )
            print(
                "Dann müssen wir die Roh-IDs aus home_team/guest_team "
                "explizit in den Match-Cache übernehmen."
            )
        else:
            print(
                f"Unerwartete Zuordnung: {direct}"
            )

        print()
        print("=" * 100)
        print("DIAGNOSE ENDE")
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
