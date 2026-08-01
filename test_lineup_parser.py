from __future__ import annotations

from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.parsers.lineup_parser import (
    LineupParser,
)


LINEUP_HTML_PATH = Path(
    "data/temp/inspect_lineup_ajax.html"
)


def print_team(
    title: str,
    team_lineup,
) -> None:
    print()
    print("-" * 60)
    print(title)
    print("-" * 60)
    print(f"Mannschaft: {team_lineup.team_name}")
    print(f"Startelf: {len(team_lineup.starting)}")
    print(f"Ersatzbank: {len(team_lineup.substitutes)}")
    print(f"Trainer: {team_lineup.coach!r}")

    print()
    print("STARTELF")

    for player in team_lineup.starting:
        markers: list[str] = []

        if player.is_goalkeeper:
            markers.append("TW")

        if player.is_captain:
            markers.append("C")

        marker_text = (
            f" [{' / '.join(markers)}]"
            if markers
            else ""
        )

        print(
            f"{player.shirt_number!s:>2} | "
            f"{player.first_name} "
            f"{player.last_name}"
            f"{marker_text} | "
            f"{player.external_id}"
        )

    print()
    print("ERSATZBANK")

    for player in team_lineup.substitutes:
        markers: list[str] = []

        if player.is_goalkeeper:
            markers.append("TW")

        if player.is_captain:
            markers.append("C")

        marker_text = (
            f" [{' / '.join(markers)}]"
            if markers
            else ""
        )

        print(
            f"{player.shirt_number!s:>2} | "
            f"{player.first_name} "
            f"{player.last_name}"
            f"{marker_text} | "
            f"{player.external_id}"
        )


def main() -> None:
    if not LINEUP_HTML_PATH.exists():
        raise FileNotFoundError(
            "Die gespeicherte AJAX-Aufstellung wurde "
            "nicht gefunden:\n"
            f"{LINEUP_HTML_PATH}"
        )

    html = LINEUP_HTML_PATH.read_text(
        encoding="utf-8"
    )

    browser = FussballDeBrowser()

    try:
        browser.start(
            headless=True,
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite wurde nicht erstellt."
            )

        parser = LineupParser(
            request_context=browser.page.request,
        )

        lineup = parser.parse(
            html
        )

        print()
        print("=" * 60)
        print("LINEUP PARSER TEST")
        print("=" * 60)

        print_team(
            title="HEIM",
            team_lineup=lineup.home,
        )

        print_team(
            title="AUSWÄRTS",
            team_lineup=lineup.away,
        )

        print()
        print("=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)
        print(
            "Spieler gesamt: "
            f"{len(lineup.home.starting)} "
            f"+ {len(lineup.home.substitutes)} "
            f"+ {len(lineup.away.starting)} "
            f"+ {len(lineup.away.substitutes)}"
        )

    finally:
        browser.close()


if __name__ == "__main__":
    main()