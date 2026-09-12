from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/database/kreisligamanager.db")

COMPETITION_NAME = "Kreisliga B11"
TEAM_NAME = "FSG Ehrang-Pfalzel"

GOAL_EVENT_CODES = (
    "GOAL",
    "PENALTY_GOAL",
    "OWN_GOAL",
)


def normalize_minute(value) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        minute = value
    else:
        text = str(value).strip()

        if not text:
            return None

        if "+" in text:
            text = text.split("+", 1)[0].strip()

        try:
            minute = int(text)
        except ValueError:
            return None

    if minute < 0:
        return None

    return min(minute, 90)


def resolve_scoring_team_id(
    event_type: str,
    event_team_id: int | None,
    home_team_id: int,
    away_team_id: int,
) -> int | None:
    if event_team_id is None:
        return None

    event_type = str(event_type).upper()

    if event_type == "OWN_GOAL":
        if event_team_id == home_team_id:
            return away_team_id

        if event_team_id == away_team_id:
            return home_team_id

        return None

    if event_team_id in (
        home_team_id,
        away_team_id,
    ):
        return event_team_id

    return None


def get_competition_id(
    cursor: sqlite3.Cursor,
) -> int:
    cursor.execute(
        """
        SELECT competition_id, name
        FROM competitions
        WHERE name = ? COLLATE NOCASE
        ORDER BY competition_id DESC
        """,
        (COMPETITION_NAME,),
    )

    rows = cursor.fetchall()

    if not rows:
        raise RuntimeError(
            f"Wettbewerb nicht gefunden: {COMPETITION_NAME}"
        )

    if len(rows) > 1:
        print(
            "WARNUNG: Mehrere Wettbewerbe mit diesem Namen gefunden. "
            f"Verwendet wird competition_id={rows[0][0]}."
        )

    return int(rows[0][0])


def get_team_id(
    cursor: sqlite3.Cursor,
    competition_id: int,
) -> int:
    cursor.execute(
        """
        SELECT
            teams.team_id,
            teams.name
        FROM competition_teams
        INNER JOIN teams
            ON teams.team_id = competition_teams.team_id
        WHERE
            competition_teams.competition_id = ?
            AND teams.name = ? COLLATE NOCASE
        LIMIT 1
        """,
        (
            competition_id,
            TEAM_NAME,
        ),
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            f"Mannschaft nicht gefunden: {TEAM_NAME}"
        )

    return int(row[0])


def load_matches(
    cursor: sqlite3.Cursor,
    competition_id: int,
    team_id: int,
) -> list[sqlite3.Row]:
    cursor.execute(
        """
        SELECT
            matches.match_id,
            matches.matchday,
            matches.match_date,
            matches.home_team_id,
            matches.away_team_id,
            matches.home_goals,
            matches.away_goals,
            home_team.name AS home_team_name,
            away_team.name AS away_team_name,
            matches.status
        FROM matches
        INNER JOIN teams AS home_team
            ON home_team.team_id = matches.home_team_id
        INNER JOIN teams AS away_team
            ON away_team.team_id = matches.away_team_id
        WHERE
            matches.competition_id = ?
            AND (
                matches.home_team_id = ?
                OR matches.away_team_id = ?
            )
            AND matches.home_goals IS NOT NULL
            AND matches.away_goals IS NOT NULL
        ORDER BY
            COALESCE(matches.matchday, 9999),
            COALESCE(matches.match_date, ''),
            matches.match_id
        """,
        (
            competition_id,
            team_id,
            team_id,
        ),
    )

    return cursor.fetchall()


def load_goal_events(
    cursor: sqlite3.Cursor,
    match_id: int,
) -> list[sqlite3.Row]:
    placeholders = ", ".join(
        "?"
        for _ in GOAL_EVENT_CODES
    )

    cursor.execute(
        f"""
        SELECT
            events.event_id,
            events.minute,
            events.team_id,
            event_types.code
        FROM events
        INNER JOIN event_types
            ON event_types.event_type_id = events.event_type_id
        WHERE
            events.match_id = ?
            AND event_types.code IN ({placeholders})
        ORDER BY
            events.minute,
            events.event_id
        """,
        (
            match_id,
            *GOAL_EVENT_CODES,
        ),
    )

    return cursor.fetchall()


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        competition_id = get_competition_id(
            cursor
        )
        team_id = get_team_id(
            cursor,
            competition_id,
        )

        print("=" * 110)
        print("TOR-TIMELINE-CHECK")
        print("=" * 110)
        print(
            f"Wettbewerb: {COMPETITION_NAME} "
            f"(competition_id={competition_id})"
        )
        print(
            f"Mannschaft:  {TEAM_NAME} "
            f"(team_id={team_id})"
        )
        print("=" * 110)

        matches = load_matches(
            cursor,
            competition_id,
            team_id,
        )

        expected_total_against = 0
        valid_total_against = 0
        raw_total_against = 0
        missing_total = 0

        for match in matches:
            match_id = int(match["match_id"])
            home_team_id = int(
                match["home_team_id"]
            )
            away_team_id = int(
                match["away_team_id"]
            )

            home_goals = int(
                match["home_goals"]
            )
            away_goals = int(
                match["away_goals"]
            )

            if team_id == home_team_id:
                expected_against = away_goals
            else:
                expected_against = home_goals

            expected_total_against += expected_against

            goal_events = load_goal_events(
                cursor,
                match_id,
            )

            against_events = []
            invalid_minute_events = []
            unassigned_events = []

            for event in goal_events:
                event_team_id = (
                    int(event["team_id"])
                    if event["team_id"] is not None
                    else None
                )

                scoring_team_id = (
                    resolve_scoring_team_id(
                        event_type=event["code"],
                        event_team_id=event_team_id,
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                    )
                )

                if scoring_team_id is None:
                    unassigned_events.append(
                        event
                    )
                    continue

                if scoring_team_id == team_id:
                    continue

                raw_total_against += 1

                minute = normalize_minute(
                    event["minute"]
                )

                if minute is None:
                    invalid_minute_events.append(
                        event
                    )
                    continue

                against_events.append(
                    (
                        event,
                        minute,
                    )
                )

            valid_against = len(
                against_events
            )
            valid_total_against += valid_against

            missing = (
                expected_against
                - valid_against
            )

            if missing > 0:
                missing_total += missing

            print()
            print(
                f"ST {str(match['matchday'] or '-'):>2} | "
                f"{match['home_team_name']} "
                f"{home_goals}:{away_goals} "
                f"{match['away_team_name']}"
            )
            print(
                f"    Erwartete Gegentore: {expected_against} | "
                f"Timeline-verwertbar: {valid_against} | "
                f"Differenz: {missing:+d}"
            )

            if against_events:
                print(
                    "    Verwertbare Gegentor-Events:"
                )

                for event, minute in against_events:
                    print(
                        "      "
                        f"event_id={event['event_id']} | "
                        f"Typ={event['code']} | "
                        f"Minute={event['minute']!r} "
                        f"-> {minute} | "
                        f"team_id={event['team_id']}"
                    )

            if invalid_minute_events:
                print(
                    "    Gegentor-Events OHNE verwertbare Minute:"
                )

                for event in invalid_minute_events:
                    print(
                        "      "
                        f"event_id={event['event_id']} | "
                        f"Typ={event['code']} | "
                        f"Minute={event['minute']!r} | "
                        f"team_id={event['team_id']}"
                    )

            if unassigned_events:
                print(
                    "    Tor-Events ohne eindeutige Mannschaftszuordnung:"
                )

                for event in unassigned_events:
                    print(
                        "      "
                        f"event_id={event['event_id']} | "
                        f"Typ={event['code']} | "
                        f"Minute={event['minute']!r} | "
                        f"team_id={event['team_id']}"
                    )

        print()
        print("=" * 110)
        print("GESAMT")
        print("=" * 110)
        print(
            f"Gegentore laut Spielergebnissen:        "
            f"{expected_total_against}"
        )
        print(
            f"Gegentor-Events insgesamt zugeordnet:   "
            f"{raw_total_against}"
        )
        print(
            f"Timeline-verwertbare Gegentor-Events:    "
            f"{valid_total_against}"
        )
        print(
            f"Fehlende Gegentore in der Timeline:      "
            f"{missing_total}"
        )
        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
