from __future__ import annotations

from pathlib import Path

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.parsers.lineup_parser import (
    LineupParser,
)


MATCH_ID = (
    "031BG6B7PG000000VS5489BUVUR5FS5A"
)

MATCH_URL = (
    "https://www.fussball.de/spiel/"
    "fc-energie-cottbus-hannover-96/-/spiel/"
    f"{MATCH_ID}#!/"
)

LINEUP_URL = (
    "https://www.fussball.de/"
    "ajax.match.lineup/"
    "-/mode/PAGE/spiel/"
    f"{MATCH_ID}/"
    "ticker-id/selectedTickerId"
)

DEBUG_PATH = Path(
    "debug/lineup"
) / f"{MATCH_ID}.html"


def print_team(
    title: str,
    team,
) -> None:
    print("=" * 100)
    print(title)
    print("=" * 100)

    print(
        f"Teamname:      {team.team_name!r}"
    )
    print(
        f"Startelf:      {len(team.starting)}"
    )
    print(
        f"Ersatzspieler: {len(team.substitutes)}"
    )
    print(
        f"Spieler gesamt:{len(team.players)}"
    )
    print(
        f"Trainer:       {team.coach!r}"
    )
    print()

    print("STARTELF")
    print("-" * 100)

    for index, player in enumerate(
        team.starting,
        start=1,
    ):
        print_player(
            index=index,
            player=player,
        )

    print()
    print("ERSATZSPIELER")
    print("-" * 100)

    for index, player in enumerate(
        team.substitutes,
        start=1,
    ):
        print_player(
            index=index,
            player=player,
        )

    print()


def print_player(
    index: int,
    player,
) -> None:
    name = " ".join(
        part
        for part in (
            player.first_name,
            player.last_name,
        )
        if part
    )

    print(
        f"{index:>2}. "
        f"{name or '-':<40} | "
        f"external_id={player.external_id or '-'} | "
        f"Nr={player.shirt_number} | "
        f"TW={player.is_goalkeeper}"
    )


def main() -> None:
    print("=" * 100)
    print("DIAGNOSE LINEUP SPIEL 789")
    print("=" * 100)
    print(
        f"Spiel-ID:   {MATCH_ID}"
    )
    print(
        f"Match-URL:  {MATCH_URL}"
    )
    print(
        f"Lineup-URL: {LINEUP_URL}"
    )
    print()

    browser = FussballDeBrowser()

    try:
        browser.start(
            headless=True,
        )

        browser.open(
            MATCH_URL
        )

        if browser.page is None:
            raise RuntimeError(
                "Browserseite nicht verfügbar."
            )

        response = browser.page.request.get(
            LINEUP_URL,
            timeout=60_000,
        )

        print("HTTP")
        print("-" * 100)
        print(
            f"Status: {response.status}"
        )
        print(
            f"OK:     {response.ok}"
        )
        print()

        html = response.text()

        print(
            f"HTML-Länge: {len(html)} Zeichen"
        )

        DEBUG_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        DEBUG_PATH.write_text(
            html,
            encoding="utf-8",
        )

        print(
            f"Debug gespeichert: {DEBUG_PATH}"
        )
        print()

        print("HTML-SCHLÜSSELWÖRTER")
        print("-" * 100)

        lower_html = html.casefold()

        for keyword in (
            "aufstellung",
            "startelf",
            "ersatzbank",
            "energie cottbus",
            "hannover 96",
            "tolcay",
            "neubauer",
            "butler",
            "player",
            "lineup",
        ):
            print(
                f"{keyword:<20}: "
                f"{lower_html.count(keyword.casefold())}"
            )

        print()

        parser = LineupParser(
            request_context=browser.page.request,
        )

        lineup = parser.parse(
            html
        )

        print_team(
            "HEIM",
            lineup.home,
        )

        print_team(
            "AUSWÄRTS",
            lineup.away,
        )

        total_players = (
            len(lineup.home.players)
            + len(lineup.away.players)
        )

        print("=" * 100)

        if total_players == 0:
            print(
                "ERGEBNIS: Endpoint liefert HTML, "
                "aber LineupParser erkennt 0 Spieler."
            )
        else:
            print(
                "ERGEBNIS: LineupParser erkennt "
                f"{total_players} Spieler."
            )

        print("=" * 100)

    finally:
        browser.close()


if __name__ == "__main__":
    main()
