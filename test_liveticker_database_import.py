from __future__ import annotations

import sqlite3
import traceback

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.match_detail_importer import (
    MatchDetailImporter,
)


DATABASE_PATH = (
    "data/database/kreisligamanager.db"
)

MATCH_ID = (
    "02TKDR2LFG000000VS5489BUVUD1610F"
)

MATCH_URL = (
    "https://www.fussball.de/spiel/-/spiel/"
    f"{MATCH_ID}/"
)

HEADLESS = False


def load_match(
    connection: sqlite3.Connection,
) -> tuple | None:
    return connection.execute(
        """
        SELECT
            matches.match_id,
            matches.external_id,
            home_teams.name,
            away_teams.name,
            matches.home_goals,
            matches.away_goals,
            matches.detail_imported,
            matches.competition_id

        FROM matches

        INNER JOIN teams AS home_teams
            ON home_teams.team_id =
                matches.home_team_id

        INNER JOIN teams AS away_teams
            ON away_teams.team_id =
                matches.away_team_id

        WHERE matches.external_id = ?;
        """,
        (
            MATCH_ID,
        ),
    ).fetchone()


def load_event_counts(
    connection: sqlite3.Connection,
    internal_match_id: int,
) -> list[tuple]:
    return connection.execute(
        """
        SELECT
            event_types.code,
            COUNT(*) AS event_count,
            COUNT(events.player_id)
                AS assigned_players,
            COUNT(DISTINCT events.team_id)
                AS assigned_teams

        FROM events

        INNER JOIN event_types
            ON event_types.event_type_id =
                events.event_type_id

        WHERE events.match_id = ?

        GROUP BY event_types.code

        ORDER BY event_types.code;
        """,
        (
            internal_match_id,
        ),
    ).fetchall()


def print_match(
    title: str,
    match_row: tuple,
) -> None:
    (
        internal_match_id,
        external_id,
        home_team,
        away_team,
        home_goals,
        away_goals,
        detail_imported,
        competition_id,
    ) = match_row

    print()
    print("=" * 90)
    print(title)
    print("=" * 90)
    print(
        f"Interne Spiel-ID:      "
        f"{internal_match_id}"
    )
    print(
        f"Externe Spiel-ID:      "
        f"{external_id}"
    )
    print(
        f"Wettbewerb-ID:         "
        f"{competition_id}"
    )
    print(
        f"Partie:                "
        f"{home_team} - {away_team}"
    )
    print(
        f"Ergebnis:              "
        f"{home_goals}:{away_goals}"
    )
    print(
        f"Detailimport:          "
        f"{detail_imported}"
    )


def print_event_counts(
    event_counts: list[tuple],
) -> None:
    print()
    print("EVENTS IN DER DATENBANK")
    print("-" * 90)

    if not event_counts:
        print(
            "Keine Events vorhanden."
        )
        return

    for (
        event_code,
        event_count,
        assigned_players,
        assigned_teams,
    ) in event_counts:
        print(
            f"{event_code:20} "
            f"Anzahl={event_count:<3} "
            f"Spieler={assigned_players:<3} "
            f"Teams={assigned_teams}"
        )


def validate_database_result(
    connection: sqlite3.Connection,
    internal_match_id: int,
) -> None:
    rows = connection.execute(
        """
        SELECT
            event_types.code,
            COUNT(*) AS event_count,
            COUNT(events.player_id)
                AS assigned_players,
            COUNT(events.team_id)
                AS assigned_teams

        FROM events

        INNER JOIN event_types
            ON event_types.event_type_id =
                events.event_type_id

        WHERE events.match_id = ?

        GROUP BY event_types.code;
        """,
        (
            internal_match_id,
        ),
    ).fetchall()

    counts = {
        str(code): {
            "count": int(count),
            "players": int(players),
            "teams": int(teams),
        }
        for (
            code,
            count,
            players,
            teams,
        ) in rows
    }

    assert counts.get(
        "GOAL",
        {},
    ).get(
        "count",
        0,
    ) == 5, (
        "Es wurden nicht genau 2 Tore importiert."
    )

    assert counts.get(
        "YELLOW_CARD",
        {},
    ).get(
        "count",
        0,
    ) == 1, (
        "Es wurden nicht genau 2 Gelbe Karten "
        "importiert."
    )

    assert counts.get(
        "SUBSTITUTION_IN",
        {},
    ).get(
        "count",
        0,
    ) == 10, (
        "Es wurden nicht genau 5 Einwechslungen "
        "importiert."
    )

    assert counts.get(
        "SUBSTITUTION_OUT",
        {},
    ).get(
        "count",
        0,
    ) == 10, (
        "Es wurden nicht genau 5 Auswechslungen "
        "importiert."
    )

    for code in (
        "GOAL",
        "YELLOW_CARD",
        "SUBSTITUTION_IN",
        "SUBSTITUTION_OUT",
    ):
        assert counts.get(
            code,
            {},
        ).get(
            "players",
            0,
        ) == counts.get(
            code,
            {},
        ).get(
            "count",
            0,
        ), (
            f"{code}: Nicht alle Events besitzen "
            "eine Spielerzuordnung."
        )

        assert counts.get(
            code,
            {},
        ).get(
            "teams",
            0,
        ) == counts.get(
            code,
            {},
        ).get(
            "count",
            0,
        ), (
            f"{code}: Nicht alle Events besitzen "
            "eine Mannschaftszuordnung."
        )


def main() -> None:
    print("=" * 90)
    print("MATCH DETAIL + LIVETICKER DATENBANKTEST")
    print("=" * 90)
    print(
        f"Spiel-ID: {MATCH_ID}"
    )
    print(
        f"URL:      {MATCH_URL}"
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    browser = FussballDeBrowser()

    try:
        match_before = load_match(
            connection
        )

        if match_before is None:
            print()
            print(
                "TEST ABGEBROCHEN"
            )
            print(
                "Das Spiel befindet sich noch nicht "
                "in der Datenbank."
            )
            print(
                "Importiere zuerst die Staffel, zu der "
                "dieses Spiel gehört."
            )
            return

        internal_match_id = int(
            match_before[0]
        )

        print_match(
            "VOR DEM IMPORT",
            match_before,
        )

        print_event_counts(
            load_event_counts(
                connection,
                internal_match_id,
            )
        )

        browser.start(
            headless=HEADLESS,
        )

        if browser.page is None:
            raise RuntimeError(
                "Die Browserseite wurde nicht erstellt."
            )

        importer = MatchDetailImporter(
            connection
        )

        result = importer.import_from_page(
            page=browser.page,
            source_url=MATCH_URL,
        )

        print()
        print("=" * 90)
        print("IMPORTERGEBNIS")
        print("=" * 90)

        for key, value in result.items():
            print(
                f"{key:30} {value}"
            )

        match_after = load_match(
            connection
        )

        if match_after is None:
            raise RuntimeError(
                "Das Spiel wurde nach dem Import "
                "nicht mehr gefunden."
            )

        print_match(
            "NACH DEM IMPORT",
            match_after,
        )

        event_counts = load_event_counts(
            connection,
            internal_match_id,
        )

        print_event_counts(
            event_counts
        )

        validate_database_result(
            connection,
            internal_match_id,
        )

        assert (
            result.get(
                "event_source"
            )
            == "liveticker_json"
        ), (
            "Der Import hat nicht die "
            "Liveticker-JSON-Quelle verwendet."
        )

        print()
        print("=" * 90)
        print(
            "LIVETICKER-DATENBANKTEST "
            "ERFOLGREICH"
        )
        print("=" * 90)

    except Exception as error:
        print()
        print("=" * 90)
        print(
            "LIVETICKER-DATENBANKTEST "
            "FEHLGESCHLAGEN"
        )
        print("=" * 90)
        print(
            f"Fehler: {error}"
        )
        print()
        traceback.print_exc()

    finally:
        browser.close()
        connection.close()

        print()
        input(
            "Zum Beenden ENTER drücken ..."
        )


if __name__ == "__main__":
    main()