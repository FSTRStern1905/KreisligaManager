from __future__ import annotations

from src.database.database import Database
from src.database.repositories.match_repository import MatchRepository
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
    repository = MatchRepository(connection)

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

        checked = 0
        correct = 0
        differences = 0
        missing_in_db = 0
        without_result = 0

        print()
        print("=" * 78)
        print("SPIELPLAN ↔ DATENBANK ERGEBNISCHECK")
        print("=" * 78)

        for source_match in schedule.matches:
            if (
                source_match.home_score is None
                or source_match.away_score is None
            ):
                without_result += 1
                continue

            checked += 1

            db_match = repository.get_by_external_id(
                source_match.match_id
            )

            if db_match is None:
                missing_in_db += 1

                print()
                print(
                    f"[FEHLT IN DB] Spieltag "
                    f"{source_match.matchday} | "
                    f"{source_match.home_team} - "
                    f"{source_match.away_team}"
                )
                print(
                    "  FUSSBALL.DE: "
                    f"{source_match.home_score}:"
                    f"{source_match.away_score}"
                )
                print(
                    f"  External-ID: {source_match.match_id}"
                )
                continue

            db_result = (
                db_match.home_goals,
                db_match.away_goals,
            )
            source_result = (
                source_match.home_score,
                source_match.away_score,
            )

            if db_result == source_result:
                correct += 1
                continue

            differences += 1

            print()
            print(
                f"[ABWEICHUNG] Spieltag "
                f"{source_match.matchday} | "
                f"{source_match.home_team} - "
                f"{source_match.away_team}"
            )
            print(
                "  FUSSBALL.DE: "
                f"{source_match.home_score}:"
                f"{source_match.away_score}"
            )
            print(
                "  Datenbank:   "
                f"{db_match.home_goals}:"
                f"{db_match.away_goals}"
            )
            print(
                f"  External-ID: {source_match.match_id}"
            )

        print()
        print("=" * 78)
        print("ZUSAMMENFASSUNG")
        print("=" * 78)
        print(
            f"Spiele mit Ergebnis geprüft: {checked}"
        )
        print(
            f"Ergebnis identisch: {correct}/{checked}"
        )
        print(
            f"Abweichende Ergebnisse: {differences}"
        )
        print(
            f"Im Spielplan, aber nicht in DB: {missing_in_db}"
        )
        print(
            f"Spiele ohne Endergebnis: {without_result}"
        )

    finally:
        browser.close()
        database.close()


if __name__ == "__main__":
    main()
