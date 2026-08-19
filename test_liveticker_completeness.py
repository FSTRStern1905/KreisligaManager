from __future__ import annotations

import sqlite3
from pathlib import Path

from src.services.liveticker_completeness_service import (
    LivetickerCompletenessService,
)


DB_PATH = Path(
    "data/database/kreisligamanager.db"
)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    try:
        service = LivetickerCompletenessService(
            connection
        )
        results = service.get_all()

        print("=" * 78)
        print("LIVETICKER-VOLLSTÄNDIGKEIT")
        print("=" * 78)

        incomplete = [
            result
            for result in results
            if not result.is_complete
        ]

        for result in incomplete:
            print()
            print(
                f"[{result.status}] "
                f"Spieltag {result.matchday} | "
                f"{result.home_team} - "
                f"{result.away_team}"
            )
            print(
                "  Offizielles Ergebnis: "
                f"{result.home_goals}:"
                f"{result.away_goals}"
            )
            print(
                "  Tor-Events:           "
                f"{result.imported_home_goals}:"
                f"{result.imported_away_goals}"
            )
            print(
                f"  Erwartete Tore:       "
                f"{result.expected_goals}"
            )
            print(
                f"  Tor-Events vorhanden: "
                f"{result.imported_goals}"
            )
            print(
                f"  Fehlende Tor-Events:  "
                f"{result.missing_goals}"
            )

            if result.extra_goals:
                print(
                    f"  Zusätzliche Tor-Events:"
                    f" {result.extra_goals}"
                )

            print(
                f"  External-ID: "
                f"{result.external_id}"
            )

        print()
        print("=" * 78)
        print("ZUSAMMENFASSUNG")
        print("=" * 78)
        print(
            f"Detailspiele geprüft: {len(results)}"
        )
        print(
            "Liveticker vollständig: "
            f"{len(results) - len(incomplete)}/"
            f"{len(results)}"
        )
        print(
            "Liveticker unvollständig: "
            f"{len(incomplete)}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
