from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.match_detail_importer import MatchDetailImporter


DB_PATH = Path("data/database/kreisligamanager.db")
BACKUP_DIR = Path("data/database/backups")

MATCH_EXTERNAL_ID = "02TNB07KSO000000VS5489BUVSSD35NB"

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "sg-kenn-fsv-trier-tarforst-ii/"
    "-/spiel/"
    f"{MATCH_EXTERNAL_ID}"
)

SG_KENN_TEAM_ID = 6
TARFORST_TEAM_ID = 4

LUCA_WELTER_EXTERNAL_ID = "00L54A77PK000000VV0AG85VVV79K56V"
ALADIN_SHALLAR_EXTERNAL_ID = "029G5Q9M9O000000VS541L4JVSOT1AHA"

DAVID_FIEGLER_EXTERNAL_ID = "017Q2O28RS000000VV0AG811VVJU4E04"
JAKOB_SCHAEFER_EXTERNAL_ID = "030662DRHC00000BVS5489C0VTR45H4I"


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
        / f"kreisligamanager_before_match_170_{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    return backup_path


def get_player_by_external_id(
    connection: sqlite3.Connection,
    external_id: str,
) -> sqlite3.Row | None:
    return connection.execute(
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
            external_id,
            external_id,
        ),
    ).fetchone()


def get_all_substitution_rows(
    connection: sqlite3.Connection,
    match_id: int,
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
            p.external_id,
            e.related_player_id,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        LEFT JOIN players AS rp
            ON rp.player_id = e.related_player_id
        WHERE
            e.match_id = ?
            AND et.code IN (
                'SUBSTITUTION_IN',
                'SUBSTITUTION_OUT'
            )
        ORDER BY
            e.minute,
            e.event_id
        """,
        (match_id,),
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
        int(row["team_id"]): int(
            row["starters"] or 0
        )
        for row in rows
        if row["team_id"] is not None
    }


def count_substitutions_by_team(
    rows: list[sqlite3.Row],
) -> dict[int, dict[str, int]]:
    result: dict[int, dict[str, int]] = {}

    for row in rows:
        if row["team_id"] is None:
            continue

        team_id = int(row["team_id"])

        if team_id not in result:
            result[team_id] = {
                "SUBSTITUTION_IN": 0,
                "SUBSTITUTION_OUT": 0,
            }

        code = str(row["code"])

        if code in result[team_id]:
            result[team_id][code] += 1

    return result


def find_event(
    rows: list[sqlite3.Row],
    *,
    player_id: int,
    code: str,
    minute: int,
    team_id: int,
    related_player_id: int,
) -> sqlite3.Row | None:
    matches = [
        row
        for row in rows
        if int(row["player_id"] or 0)
        == player_id
        and row["code"] == code
        and int(row["minute"] or 0)
        == minute
        and int(row["team_id"] or 0)
        == team_id
        and int(
            row["related_player_id"] or 0
        )
        == related_player_id
    ]

    if len(matches) != 1:
        return None

    return matches[0]


def main() -> None:
    print("=" * 94)
    print(
        "HAUPT-DB REIMPORT: SPIEL 170"
    )
    print("=" * 94)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Haupt-DB fehlt: {DB_PATH}"
        )

    backup_path = create_backup()

    print(f"Haupt-DB: {DB_PATH}")
    print(f"Backup:   {backup_path}")
    print(
        "Es wird ausschließlich Spiel 170 "
        "reimportiert."
    )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    browser = FussballDeBrowser()

    try:
        match = connection.execute(
            """
            SELECT
                match_id,
                matchday,
                home_team_id,
                away_team_id
            FROM matches
            WHERE external_id = ?
            LIMIT 1
            """,
            (MATCH_EXTERNAL_ID,),
        ).fetchone()

        if match is None:
            raise RuntimeError(
                "Spiel 170 wurde nicht gefunden."
            )

        match_id = int(
            match["match_id"]
        )

        print()
        print("MATCH")
        print("-" * 94)
        print(dict(match))

        before = get_all_substitution_rows(
            connection,
            match_id,
        )

        print()
        print("VOR REIMPORT")
        print("-" * 94)

        for row in before:
            print(dict(row))

        browser.start(
            headless=False,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite konnte nicht "
                "erstellt werden."
            )

        importer = MatchDetailImporter(
            connection
        )

        result = importer.import_from_page(
            page=browser.page,
            source_url=MATCH_URL,
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

        after = get_all_substitution_rows(
            connection,
            match_id,
        )

        print()
        print("NACH REIMPORT")
        print("-" * 94)

        for row in after:
            print(dict(row))

        starter_counts = get_starter_counts(
            connection,
            match_id,
        )

        print()
        print("STARTER")
        print("-" * 94)
        print(starter_counts)

        counts = count_substitutions_by_team(
            after
        )

        print()
        print("WECHSELZÄHLUNG")
        print("-" * 94)
        print(counts)

        luca = get_player_by_external_id(
            connection,
            LUCA_WELTER_EXTERNAL_ID,
        )

        aladin = get_player_by_external_id(
            connection,
            ALADIN_SHALLAR_EXTERNAL_ID,
        )

        david = get_player_by_external_id(
            connection,
            DAVID_FIEGLER_EXTERNAL_ID,
        )

        jakob = get_player_by_external_id(
            connection,
            JAKOB_SCHAEFER_EXTERNAL_ID,
        )

        missing_players = [
            name
            for name, player in (
                ("Luca Welter", luca),
                ("Aladin Shallar", aladin),
                ("David Fiegler", david),
                ("Jakob Schäfer", jakob),
            )
            if player is None
        ]

        if missing_players:
            raise RuntimeError(
                "Zielspieler nicht gefunden: "
                + ", ".join(
                    missing_players
                )
            )

        luca_id = int(
            luca["player_id"]
        )

        aladin_id = int(
            aladin["player_id"]
        )

        david_id = int(
            david["player_id"]
        )

        jakob_id = int(
            jakob["player_id"]
        )

        kenn_out = find_event(
            after,
            player_id=luca_id,
            code="SUBSTITUTION_OUT",
            minute=45,
            team_id=SG_KENN_TEAM_ID,
            related_player_id=aladin_id,
        )

        kenn_in = find_event(
            after,
            player_id=aladin_id,
            code="SUBSTITUTION_IN",
            minute=45,
            team_id=SG_KENN_TEAM_ID,
            related_player_id=luca_id,
        )

        tarforst_out = find_event(
            after,
            player_id=david_id,
            code="SUBSTITUTION_OUT",
            minute=74,
            team_id=TARFORST_TEAM_ID,
            related_player_id=jakob_id,
        )

        tarforst_in = find_event(
            after,
            player_id=jakob_id,
            code="SUBSTITUTION_IN",
            minute=74,
            team_id=TARFORST_TEAM_ID,
            related_player_id=david_id,
        )

        valid_kenn_pair = (
            kenn_out is not None
            and kenn_in is not None
        )

        valid_tarforst_pair = (
            tarforst_out is not None
            and tarforst_in is not None
        )

        valid_counts = (
            counts.get(
                SG_KENN_TEAM_ID,
                {},
            ).get(
                "SUBSTITUTION_IN",
                0,
            )
            == 5
            and counts.get(
                SG_KENN_TEAM_ID,
                {},
            ).get(
                "SUBSTITUTION_OUT",
                0,
            )
            == 5
            and counts.get(
                TARFORST_TEAM_ID,
                {},
            ).get(
                "SUBSTITUTION_IN",
                0,
            )
            == 4
            and counts.get(
                TARFORST_TEAM_ID,
                {},
            ).get(
                "SUBSTITUTION_OUT",
                0,
            )
            == 4
        )

        valid_links = all(
            row["player_id"] is not None
            and row["team_id"] is not None
            and row["related_player_id"]
            is not None
            for row in after
        )

        home_team_id = int(
            match["home_team_id"]
        )

        away_team_id = int(
            match["away_team_id"]
        )

        valid_starters = (
            starter_counts.get(
                home_team_id
            )
            == 11
            and starter_counts.get(
                away_team_id
            )
            == 11
        )

        print()
        print("WECHSELPRÜFUNG")
        print("-" * 94)

        print(
            "45' SG Kenn "
            "(Aladin Shallar IN ↔ "
            "Luca Welter OUT): "
            f"{'OK' if valid_kenn_pair else 'FEHLER'}"
        )

        print(
            "74' FSV Trier-Tarforst II "
            "(Jakob Schäfer IN ↔ "
            "David Fiegler OUT): "
            f"{'OK' if valid_tarforst_pair else 'FEHLER'}"
        )

        print(
            "Wechselanzahl 5/5 und 4/4: "
            f"{'OK' if valid_counts else 'FEHLER'}"
        )

        print(
            "Alle Wechsel mit "
            "player_id/team_id/"
            "related_player_id: "
            f"{'OK' if valid_links else 'FEHLER'}"
        )

        print(
            "Starter 11/11: "
            f"{'OK' if valid_starters else 'FEHLER'}"
        )

        print()
        print("=" * 94)

        if (
            valid_kenn_pair
            and valid_tarforst_pair
            and valid_counts
            and valid_links
            and valid_starters
        ):
            connection.commit()

            print(
                "ERGEBNIS: SPIEL 170 "
                "REIMPORT ERFOLGREICH."
            )

            print(
                "Änderungen wurden in die "
                "Haupt-DB übernommen."
            )

            print(
                "Alle Wechselpaare sind "
                "vollständig und konsistent."
            )

        else:
            connection.rollback()

            print(
                "ERGEBNIS: SPIEL 170 "
                "REIMPORT ABGEBROCHEN."
            )

            print(
                "Änderungen wurden NICHT "
                "in die Haupt-DB übernommen."
            )

            if not valid_kenn_pair:
                print(
                    "Fehler: Wechselpaar "
                    "SG Kenn bei 45' "
                    "ist nicht korrekt."
                )

            if not valid_tarforst_pair:
                print(
                    "Fehler: Wechselpaar "
                    "Tarforst bei 74' "
                    "ist nicht korrekt."
                )

            if not valid_counts:
                print(
                    "Fehler: IN/OUT-Zählung "
                    "ist nicht ausgeglichen."
                )

            if not valid_links:
                print(
                    "Fehler: Mindestens ein "
                    "Wechsel hat fehlende IDs."
                )

            if not valid_starters:
                print(
                    "Fehler: Starterprüfung "
                    "nicht bestanden."
                )

            raise RuntimeError(
                "Qualitätsprüfung für "
                "Spiel 170 nicht bestanden."
            )

        print("=" * 94)

    except Exception:
        connection.rollback()
        raise

    finally:
        browser.close()
        connection.close()


if __name__ == "__main__":
    main()