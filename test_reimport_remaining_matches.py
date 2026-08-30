from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.match_detail_importer import MatchDetailImporter


SOURCE_DB = Path("data/database/kreisligamanager.db")
TEST_DB = Path("data/database/remaining_matches_reimport_test.db")


@dataclass(frozen=True)
class MatchCase:
    match_id: int
    match_external_id: str
    match_url: str
    target_player_external_id: str
    expected_first_name: str
    expected_last_name: str
    expected_minute: int
    expected_team_id: int


CASES = (
    MatchCase(
        match_id=13,
        match_external_id="02TNB07CG0000000VS5489BUVSSD35NB",
        match_url=(
            "https://www.fussball.de/spiel/"
            "djk-st-matthias-trier-sg-serrig/"
            "-/spiel/"
            "02TNB07CG0000000VS5489BUVSSD35NB"
        ),
        target_player_external_id="00L54A59RO000000VV0AG85VVV79K56V",
        expected_first_name="Slawa",
        expected_last_name="Sauer",
        expected_minute=0,
        expected_team_id=8,
    ),
    MatchCase(
        match_id=30,
        match_external_id="02TNB07D30000000VS5489BUVSSD35NB",
        match_url=(
            "https://www.fussball.de/spiel/"
            "vfl-trier-sg-kenn/"
            "-/spiel/"
            "02TNB07D30000000VS5489BUVSSD35NB"
        ),
        target_player_external_id="",
        expected_first_name="Jan",
        expected_last_name="Wagner",
        expected_minute=90,
        expected_team_id=6,
    ),
    MatchCase(
        match_id=71,
        match_external_id="02TNB07EQS000000VS5489BUVSSD35NB",
        match_url=(
            "https://www.fussball.de/spiel/"
            "sg-kanzem-djk-st-matthias-trier/"
            "-/spiel/"
            "02TNB07EQS000000VS5489BUVSSD35NB"
        ),
        target_player_external_id="02J54E508C000000VUM1DNPDVV95DGRG",
        expected_first_name="Levin",
        expected_last_name="Steffes",
        expected_minute=65,
        expected_team_id=2,
    ),
)


def get_match(
    connection: sqlite3.Connection,
    case: MatchCase,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            match_id,
            matchday,
            home_team_id,
            away_team_id,
            external_id
        FROM matches
        WHERE match_id = ?
          AND external_id = ?
        LIMIT 1
        """,
        (
            case.match_id,
            case.match_external_id,
        ),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Spiel {case.match_id} wurde nicht gefunden."
        )

    return row


def get_target_player(
    connection: sqlite3.Connection,
    case: MatchCase,
) -> sqlite3.Row:
    if case.target_player_external_id:
        row = connection.execute(
            """
            SELECT
                p.player_id,
                p.first_name,
                p.last_name,
                p.external_id
            FROM players AS p
            WHERE
                p.external_id = ?
                OR EXISTS (
                    SELECT 1
                    FROM player_external_ids AS pei
                    WHERE pei.player_id = p.player_id
                      AND pei.external_id = ?
                )
            LIMIT 1
            """,
            (
                case.target_player_external_id,
                case.target_player_external_id,
            ),
        ).fetchone()

        if row is not None:
            return row

    row = connection.execute(
        """
        SELECT
            player_id,
            first_name,
            last_name,
            external_id
        FROM players
        WHERE first_name = ?
          AND last_name = ?
        LIMIT 1
        """,
        (
            case.expected_first_name,
            case.expected_last_name,
        ),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Zielspieler für Spiel {case.match_id} "
            f"nicht gefunden: "
            f"{case.expected_first_name} "
            f"{case.expected_last_name}"
        )

    return row


def get_target_events(
    connection: sqlite3.Connection,
    match_id: int,
    player_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.team_id,
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        WHERE
            e.match_id = ?
            AND e.player_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY
            e.minute,
            e.event_id
        """,
        (
            match_id,
            player_id,
        ),
    ).fetchall()


def get_starter_counts(
    connection: sqlite3.Connection,
    match_id: int,
) -> dict[int, int]:
    rows = connection.execute(
        """
        SELECT
            team_id,
            SUM(
                CASE
                    WHEN is_starting = 1
                    THEN 1
                    ELSE 0
                END
            ) AS starters
        FROM player_match_stats
        WHERE match_id = ?
        GROUP BY team_id
        ORDER BY team_id
        """,
        (match_id,),
    ).fetchall()

    return {
        int(row["team_id"]): int(row["starters"] or 0)
        for row in rows
        if row["team_id"] is not None
    }


def validate_case(
    connection: sqlite3.Connection,
    case: MatchCase,
    match: sqlite3.Row,
    player: sqlite3.Row,
) -> tuple[bool, str]:
    events = get_target_events(
        connection,
        case.match_id,
        int(player["player_id"]),
    )

    starter_counts = get_starter_counts(
        connection,
        case.match_id,
    )

    valid_event = (
        len(events) == 1
        and events[0]["code"] == "SUBSTITUTION_OUT"
        and int(events[0]["minute"] or 0)
        == case.expected_minute
        and int(events[0]["team_id"] or 0)
        == case.expected_team_id
        and events[0]["related_player_id"] is None
        and events[0]["first_name"]
        == case.expected_first_name
        and events[0]["last_name"]
        == case.expected_last_name
    )

    home_team_id = int(match["home_team_id"])
    away_team_id = int(match["away_team_id"])

    valid_starters = (
        starter_counts.get(home_team_id) == 11
        and starter_counts.get(away_team_id) == 11
    )

    print()
    print("NACH REIMPORT")
    print("-" * 94)

    for row in events:
        print(dict(row))

    print()
    print("STARTER")
    print("-" * 94)
    print(starter_counts)

    if valid_event and valid_starters:
        return (
            True,
            (
                f"{case.expected_minute}' "
                f"SUBSTITUTION_OUT "
                f"{case.expected_first_name} "
                f"{case.expected_last_name} "
                "mit related_player_id=NULL."
            ),
        )

    errors: list[str] = []

    if not valid_event:
        errors.append(
            "Zielereignis ist nicht korrekt."
        )

    if not valid_starters:
        errors.append(
            "Starterprüfung ist nicht korrekt."
        )

    return False, " ".join(errors)


def run_case(
    connection: sqlite3.Connection,
    browser: FussballDeBrowser,
    importer: MatchDetailImporter,
    case: MatchCase,
) -> tuple[bool, str]:
    print()
    print("=" * 94)
    print(
        f"SPIEL {case.match_id} "
        f"/ {case.expected_first_name} "
        f"{case.expected_last_name}"
    )
    print("=" * 94)

    match = get_match(
        connection,
        case,
    )

    player = get_target_player(
        connection,
        case,
    )

    print()
    print("MATCH")
    print("-" * 94)
    print(dict(match))

    print()
    print("ZIELSPIELER")
    print("-" * 94)
    print(dict(player))

    before = get_target_events(
        connection,
        case.match_id,
        int(player["player_id"]),
    )

    print()
    print("VOR REIMPORT")
    print("-" * 94)

    for row in before:
        print(dict(row))

    if browser.page is None:
        raise RuntimeError(
            "Browserseite konnte nicht erstellt werden."
        )

    result = importer.import_from_page(
        page=browser.page,
        source_url=case.match_url,
    )

    print()
    print("IMPORTERGEBNIS")
    print("-" * 94)
    print(
        "lineups_imported: "
        f"{result.get('lineups_imported')}"
    )
    print(
        "events_imported:  "
        f"{result.get('events_imported')}"
    )
    print(
        "event_source:     "
        f"{result.get('event_source')}"
    )

    return validate_case(
        connection,
        case,
        match,
        player,
    )


def main() -> None:
    print("=" * 94)
    print(
        "SAMMELTEST: SPIELE 13 / 30 / 71"
    )
    print("=" * 94)

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {SOURCE_DB}"
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

    connection = sqlite3.connect(TEST_DB)
    connection.row_factory = sqlite3.Row

    browser = FussballDeBrowser()
    results: list[tuple[int, bool, str]] = []

    try:
        browser.start(
            headless=False,
        )

        importer = MatchDetailImporter(
            connection
        )

        for case in CASES:
            try:
                ok, message = run_case(
                    connection,
                    browser,
                    importer,
                    case,
                )

                results.append(
                    (
                        case.match_id,
                        ok,
                        message,
                    )
                )

            except Exception as exc:
                results.append(
                    (
                        case.match_id,
                        False,
                        str(exc),
                    )
                )

        print()
        print("=" * 94)
        print("GESAMTERGEBNIS")
        print("=" * 94)

        passed = 0

        for match_id, ok, message in results:
            status = (
                "OK"
                if ok
                else "FEHLER"
            )

            if ok:
                passed += 1

            print(
                f"Spiel {match_id}: "
                f"{status} | {message}"
            )

        print("-" * 94)
        print(
            f"{passed}/{len(CASES)} SAUBER"
        )

        if passed != len(CASES):
            raise RuntimeError(
                "Nicht alle Sammeltests "
                "wurden bestanden."
            )

        print(
            "ERGEBNIS: ALLE 3 SPIELE SAUBER."
        )
        print("=" * 94)

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()
