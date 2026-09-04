from __future__ import annotations

import sys

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


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Aufruf:"
        )
        print(
            'python debug_schedule_scores.py '
            '"FUSSBALL_DE_SPIELPLAN_URL"'
        )
        sys.exit(1)

    url = sys.argv[1].strip()

    if not url:
        raise ValueError(
            "Die Spielplan-URL darf nicht leer sein."
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
