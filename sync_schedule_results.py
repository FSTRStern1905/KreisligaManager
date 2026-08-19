from __future__ import annotations

from src.database.database import Database
from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.parsers.schedule_parser import ScheduleParser


COMPETITION_URL = (
    "https://www.fussball.de/spielplan/"
    "kreisliga-a7-kreis-trier-saarburg-kreisliga-a-herren-"
    "saison2526-rheinland/-/staffel/"
    "02TN13LMJO000008VS5489BUVSSD35NB-G"
    "#!/section/matchplan"
)


def main() -> None:
    database = Database(
        database_name="kreisligamanager.db",
    )
    connection = database.connect()

    browser = FussballDeBrowser()

    try:
        browser.start(headless=False)
        browser.open(COMPETITION_URL)

        if browser.page is None:
            raise RuntimeError(
                "FUSSBALL.DE-Spielplan konnte nicht geladen werden."
            )

        schedule = ScheduleParser(
            browser.page
        ).parse()

        updated = 0
        unchanged = 0
        missing = 0
        without_result = 0

        print()
        print("=" * 78)
        print("OFFIZIELLE SPIELPLANERGEBNISSE → DATENBANK")
        print("=" * 78)

        for match in schedule.matches:
            if (
                match.home_score is None
                or match.away_score is None
            ):
                without_result += 1
                continue

            row = connection.execute(
                """
                SELECT
                    match_id,
                    home_goals,
                    away_goals
                FROM matches
                WHERE external_id = ?
                """,
                (match.match_id,),
            ).fetchone()

            if row is None:
                missing += 1
                print()
                print(
                    f"[FEHLT] Spieltag {match.matchday} | "
                    f"{match.home_team} - {match.away_team}"
                )
                continue

            old_home = row[1]
            old_away = row[2]

            if (
                old_home == match.home_score
                and old_away == match.away_score
            ):
                unchanged += 1
                continue

            connection.execute(
                """
                UPDATE matches
                SET
                    home_goals = ?,
                    away_goals = ?,
                    status = 'finished'
                WHERE external_id = ?
                """,
                (
                    match.home_score,
                    match.away_score,
                    match.match_id,
                ),
            )

            updated += 1

            print()
            print(
                f"[AKTUALISIERT] Spieltag {match.matchday} | "
                f"{match.home_team} - {match.away_team}"
            )
            print(
                f"  Alt: {old_home}:{old_away}"
            )
            print(
                f"  Neu: {match.home_score}:{match.away_score}"
            )

        connection.commit()

        print()
        print("=" * 78)
        print("ZUSAMMENFASSUNG")
        print("=" * 78)
        print(f"Aktualisiert: {updated}")
        print(f"Bereits korrekt: {unchanged}")
        print(f"Fehlt in DB: {missing}")
        print(f"Ohne Endergebnis: {without_result}")

    except Exception:
        connection.rollback()
        raise

    finally:
        browser.close()
        database.close()


if __name__ == "__main__":
    main()
