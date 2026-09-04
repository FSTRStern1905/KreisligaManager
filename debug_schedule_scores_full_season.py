from __future__ import annotations

import sys
import re

from bs4 import BeautifulSoup, Tag

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.parsers.schedule_parser import (
    ScheduleParser,
)


MAX_MATCHES = 15


def shorten(
    value: str,
    length: int = 800,
) -> str:
    normalized = " ".join(
        value.split()
    )

    if len(normalized) <= length:
        return normalized

    return (
        normalized[:length]
        + " ..."
    )



def set_full_season_range(
    page,
) -> None:
    """
    FUSSBALL.DE öffnet den Staffelspielplan teilweise mit einem
    eingeschränkten 'Von'-Datum. Für den Import erzwingen wir den
    Saisonbeginn 07.08.2026 und laden die Tabelle anschließend neu.
    """
    date_inputs = page.locator(
        "input"
    )

    matching_indexes: list[int] = []

    for index in range(
        date_inputs.count()
    ):
        locator = date_inputs.nth(
            index
        )

        try:
            value = locator.input_value().strip()
        except Exception:
            continue

        if re.fullmatch(
            r"\d{2}\.\d{2}\.\d{4}",
            value,
        ):
            matching_indexes.append(
                index
            )

    if len(
        matching_indexes
    ) < 2:
        print(
            "WARNUNG: Datumsfelder wurden "
            "nicht eindeutig gefunden."
        )
        return

    from_input = date_inputs.nth(
        matching_indexes[0]
    )

    to_input = date_inputs.nth(
        matching_indexes[1]
    )

    print(
        "Datumsbereich vorher: "
        f"{from_input.input_value()} "
        f"bis {to_input.input_value()}"
    )

    # Manche FUSSBALL.DE-Datepicker reagieren zuverlässiger auf
    # direkte JS-Wertsetzung plus input/change Events als auf fill().
    page.evaluate(
        """
        ([fromElement, toElement]) => {
            fromElement.value = '07.08.2026';
            toElement.value = '30.06.2027';

            for (const element of [fromElement, toElement]) {
                element.dispatchEvent(
                    new Event('input', { bubbles: true })
                );
                element.dispatchEvent(
                    new Event('change', { bubbles: true })
                );
            }
        }
        """,
        [
            from_input.element_handle(),
            to_input.element_handle(),
        ],
    )

    go_button = page.get_by_text(
        "LOS",
        exact=True,
    )

    if go_button.count() == 0:
        go_button = page.locator(
            "button, input[type='submit'], a"
        ).filter(
            has_text="LOS"
        )

    if go_button.count() == 0:
        raise RuntimeError(
            "Der LOS-Button für den "
            "Datumsfilter wurde nicht gefunden."
        )

    go_button.first.click()

    try:
        page.wait_for_load_state(
            "networkidle",
            timeout=10000,
        )
    except Exception:
        page.wait_for_timeout(
            2500
        )

    page.wait_for_timeout(
        1000
    )

    print(
        "Datumsbereich gesetzt: "
        "07.08.2026 bis 30.06.2027"
    )


def main() -> None:
    url = (
        "https://www.fussball.de/spielplan/"
        "regionalliga-suedwest-deutschland-"
        "regionalliga-suedwest-herren-saison2627-"
        "deutschland/-/staffel/"
        "031D0NRQ3O000004VS5489BUVUR5FS5A-G"
        "#!/section/matchplan"
    )

    browser = FussballDeBrowser()

    try:
        print(
            "Browser wird gestartet ..."
        )

        browser.start(
            headless=False,
        )

        browser.open(
            url
        )

        if browser.page is None:
            raise RuntimeError(
                "Die FUSSBALL.DE-Seite wurde "
                "nicht geladen."
            )

        set_full_season_range(
            browser.page
        )

        parser = ScheduleParser(
            browser.page
        )

        html = browser.page.content()

        soup = BeautifulSoup(
            html,
            "lxml",
        )

        table: Tag | None = None

        for selector in parser.TABLE_SELECTORS:
            candidate = soup.select_one(
                selector
            )

            if isinstance(
                candidate,
                Tag,
            ):
                table = candidate
                break

        if not isinstance(
            table,
            Tag,
        ):
            raise RuntimeError(
                "Die Spielplan-Tabelle wurde "
                "nicht gefunden."
            )

        rows = table.select(
            "tbody > tr"
        )

        print()
        print(
            "=" * 100
        )
        print(
            "SCORE-DEBUG FUSSBALL.DE"
        )
        print(
            "=" * 100
        )
        print(
            f"Tabellenzeilen: {len(rows)}"
        )
        print()

        match_counter = 0

        for row in rows:
            if not isinstance(
                row,
                Tag,
            ):
                continue

            if parser._is_headline_row(
                row
            ):
                continue

            team_cells = row.select(
                "td.column-club"
            )

            if len(team_cells) < 2:
                continue

            home_team = (
                parser._extract_team_name(
                    team_cells[0]
                )
            )

            away_team = (
                parser._extract_team_name(
                    team_cells[1]
                )
            )

            if (
                not home_team
                or not away_team
            ):
                continue

            if (
                away_team.casefold()
                == "spielfrei"
            ):
                continue

            match_counter += 1

            row_text = parser._get_text(
                row
            )

            date_cell = row.select_one(
                "td.column-date"
            )

            date_text = parser._get_text(
                date_cell
            )

            time_value = (
                parser._extract_time(
                    date_text
                )
                or parser._extract_time(
                    row_text
                )
            )

            score_cell = row.select_one(
                "td.column-score"
            )

            print(
                "-" * 100
            )
            print(
                f"[{match_counter}] "
                f"{home_team} - {away_team}"
            )
            print(
                f"ROW TEXT: "
                f"{row_text}"
            )
            print(
                f"DATUM/ZEIT: "
                f"{date_text}"
            )

            if not isinstance(
                score_cell,
                Tag,
            ):
                print(
                    "SCORE CELL: NICHT GEFUNDEN"
                )
                print()

                if (
                    match_counter
                    >= MAX_MATCHES
                ):
                    break

                continue

            decoded_score_text = (
                parser._get_text(
                    score_cell
                )
            )

            print(
                "SCORE CELL CLASSES: "
                f"{score_cell.get('class', [])}"
            )

            print(
                "SCORE CELL ATTRS: "
                f"{dict(score_cell.attrs)}"
            )

            print(
                "SCORE TEXT DECODED: "
                f"{decoded_score_text!r}"
            )

            print(
                "SCORE HTML:"
            )
            print(
                shorten(
                    str(
                        score_cell
                    ),
                    1600,
                )
            )

            print(
                "SCORE-KINDER:"
            )

            for child_index, child in enumerate(
                score_cell.find_all(
                    recursive=False
                ),
                start=1,
            ):
                if not isinstance(
                    child,
                    Tag,
                ):
                    continue

                print(
                    f"  [{child_index}] "
                    f"<{child.name}> "
                    f"class={child.get('class', [])} "
                    f"attrs={dict(child.attrs)} "
                    f"text={parser._get_text(child)!r}"
                )

            score_parts = (
                parser._extract_score_parts(
                    score_cell
                )
            )

            extracted_score = (
                parser._extract_score(
                    row=row,
                    time_value=time_value,
                )
            )

            home_score, away_score = (
                extracted_score
            )

            status = parser._extract_status(
                row_text=row_text,
                home_score=home_score,
                away_score=away_score,
            )

            print(
                "SCORE PARTS: "
                f"{score_parts}"
            )
            print(
                "PARSED SCORE: "
                f"{home_score} - {away_score}"
            )
            print(
                "STATUS: "
                f"{status}"
            )
            print()

            if (
                match_counter
                >= MAX_MATCHES
            ):
                break

        print(
            "=" * 100
        )
        print(
            f"Geprüfte Spiele: "
            f"{match_counter}"
        )
        print(
            "=" * 100
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()
