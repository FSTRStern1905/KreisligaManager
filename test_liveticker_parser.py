from __future__ import annotations

import json

from src.importer.fussballde.liveticker_parser import (
    LivetickerParser,
)


HTML_SAMPLE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>FC Beispiel - SV Muster</title>
</head>
<body>
    <div class="team-home">
        <div class="team-name">FC Beispiel</div>
    </div>

    <div class="team-away">
        <div class="team-name">SV Muster</div>
    </div>

    <div class="result">2:1</div>

    <div id="liveticker">
        <div
            class="liveticker-event"
            data-event-id="event_1"
            data-event-type="goal"
            data-team="FC Beispiel"
        >
            <div class="minute">12'</div>
            <div
                class="player-name"
                data-player-name="Max Mustermann"
                data-player-id="player_1"
            >
                Max Mustermann
            </div>
            <div class="description">
                12' Tor für FC Beispiel durch Max Mustermann.
                Neuer Spielstand 1:0.
            </div>
        </div>

        <div
            class="liveticker-event"
            data-event-id="event_2"
            data-event-type="yellow_card"
            data-team="SV Muster"
        >
            <div class="minute">34'</div>
            <div
                class="player-name"
                data-player-name="Erik Beispiel"
                data-player-id="player_2"
            >
                Erik Beispiel
            </div>
            <div class="description">
                34' Gelbe Karte für Erik Beispiel.
            </div>
        </div>

        <div
            class="liveticker-event"
            data-event-id="event_3"
            data-event-type="substitution"
            data-team="FC Beispiel"
        >
            <div class="minute">67'</div>
            <div
                class="player-name"
                data-player-name="Jonas Neu"
                data-player-id="player_3"
            >
                Jonas Neu
            </div>
            <div
                class="player-out"
                data-player-out="Lukas Alt"
            >
                Lukas Alt
            </div>
            <div class="description">
                67' Wechsel bei FC Beispiel:
                Jonas Neu kommt für Lukas Alt.
            </div>
        </div>
    </div>
</body>
</html>
"""


JSON_SAMPLE = {
    "match": {
        "title": "FC Beispiel - SV Muster",
        "competitionName": "Testliga",
        "homeTeam": {
            "name": "FC Beispiel",
        },
        "awayTeam": {
            "name": "SV Muster",
        },
        "score": {
            "home": 2,
            "away": 1,
        },
        "events": [
            {
                "id": "json_event_1",
                "minute": 12,
                "type": "goal",
                "team": {
                    "name": "FC Beispiel",
                },
                "player": {
                    "id": "player_1",
                    "name": "Max Mustermann",
                },
                "homeScore": 1,
                "awayScore": 0,
                "description": (
                    "Tor für FC Beispiel "
                    "durch Max Mustermann."
                ),
            },
            {
                "id": "json_event_2",
                "minute": 34,
                "type": "yellow_card",
                "team": {
                    "name": "SV Muster",
                },
                "player": {
                    "id": "player_2",
                    "name": "Erik Beispiel",
                },
                "description": (
                    "Gelbe Karte für Erik Beispiel."
                ),
            },
            {
                "id": "json_event_3",
                "minute": 67,
                "type": "substitution",
                "team": {
                    "name": "FC Beispiel",
                },
                "playerIn": {
                    "id": "player_3",
                    "name": "Jonas Neu",
                },
                "playerOut": {
                    "id": "player_4",
                    "name": "Lukas Alt",
                },
                "description": (
                    "Jonas Neu kommt "
                    "für Lukas Alt."
                ),
            },
        ],
    },
}


def print_result(
    title: str,
    data,
) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print(
        f"Quelle:                "
        f"{data.source_type}"
    )
    print(
        f"Liveticker erkannt:    "
        f"{'JA' if data.ticker_available else 'NEIN'}"
    )
    print(
        f"Heimteam:              "
        f"{data.home_team}"
    )
    print(
        f"Auswärtsteam:          "
        f"{data.away_team}"
    )
    print(
        f"Spielstand:            "
        f"{data.home_score}:{data.away_score}"
    )
    print(
        f"Events:                "
        f"{data.event_count}"
    )
    print(
        f"Mit Spielerzuordnung:  "
        f"{data.assigned_event_count}"
    )
    print(
        f"Ohne Spielerzuordnung: "
        f"{data.unassigned_event_count}"
    )
    print(
        f"Zuordnungsquote:       "
        f"{data.player_assignment_rate:.1f} %"
    )
    print()

    for index, event in enumerate(
        data.events,
        start=1,
    ):
        print(
            f"[{index}] "
            f"{event.display_minute}' "
            f"{event.event_type}"
        )
        print(
            f"    Mannschaft: "
            f"{event.team}"
        )
        print(
            f"    Spieler:    "
            f"{event.player}"
        )
        print(
            f"    Spieler-ID: "
            f"{event.player_id}"
        )

        if event.player_out:
            print(
                f"    Spieler raus: "
                f"{event.player_out}"
            )

        if event.has_score:
            print(
                f"    Spielstand: "
                f"{event.score_home}:"
                f"{event.score_away}"
            )

        print(
            f"    Text: "
            f"{event.description}"
        )


def validate_html_result(
    data,
) -> None:
    assert data.ticker_available
    assert data.home_team == "FC Beispiel"
    assert data.away_team == "SV Muster"
    assert data.home_score == 2
    assert data.away_score == 1
    assert data.event_count == 3

    assert (
        data.events[0].event_type
        == "goal"
    )
    assert (
        data.events[0].player
        == "Max Mustermann"
    )

    assert (
        data.events[1].event_type
        == "yellow_card"
    )
    assert (
        data.events[2].event_type
        == "substitution"
    )
    assert (
        data.events[2].player_out
        == "Lukas Alt"
    )


def validate_json_result(
    data,
) -> None:
    assert data.ticker_available
    assert data.source_type == "json"
    assert data.home_team == "FC Beispiel"
    assert data.away_team == "SV Muster"
    assert data.home_score == 2
    assert data.away_score == 1
    assert data.event_count == 3

    assert (
        data.events[0].event_type
        == "goal"
    )
    assert (
        data.events[0].player_id
        == "player_1"
    )

    assert (
        data.events[1].event_type
        == "yellow_card"
    )
    assert (
        data.events[2].event_type
        == "substitution"
    )
    assert (
        data.events[2].player_out_id
        == "player_4"
    )


def main() -> None:
    parser = LivetickerParser()

    html_result = parser.parse_html(
        html=HTML_SAMPLE,
        source_url="https://example.test/html",
        match_id="html_test_match",
    )

    print_result(
        "HTML-TEST",
        html_result,
    )

    validate_html_result(
        html_result
    )

    json_result = parser.parse_json(
        payload=JSON_SAMPLE,
        source_url="https://example.test/json",
        match_id="json_test_match",
    )

    print_result(
        "JSON-TEST",
        json_result,
    )

    validate_json_result(
        json_result
    )

    auto_html_result = parser.parse_auto(
        content=HTML_SAMPLE,
        match_id="auto_html_test",
    )

    auto_json_result = parser.parse_auto(
        content=json.dumps(
            JSON_SAMPLE,
            ensure_ascii=False,
        ),
        match_id="auto_json_test",
    )

    assert (
        auto_html_result.source_type
        == "html"
    )
    assert (
        auto_json_result.source_type
        == "json"
    )

    print()
    print("=" * 70)
    print("ALLE LIVETICKER-PARSER-TESTS ERFOLGREICH")
    print("=" * 70)


if __name__ == "__main__":
    main()