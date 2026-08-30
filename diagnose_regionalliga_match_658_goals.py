from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)
MATCH_ID = 658


def rows(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple = (),
) -> list[dict]:
    return [
        dict(row)
        for row in connection.execute(
            sql,
            params,
        ).fetchall()
    ]


def print_rows(
    title: str,
    data: list[dict],
) -> None:
    print()
    print("=" * 110)
    print(title)
    print("=" * 110)

    if not data:
        print("(keine)")
        return

    for item in data:
        print(item)


def main() -> None:
    print("=" * 110)
    print(
        "SPIEL 658 / SG SONNENHOF GROSSASPACH - "
        "FC-ASTORIA WALLDORF / TOR-DIAGNOSE"
    )
    print("=" * 110)
    print(f"Datenbank: {DB_PATH}")
    print("Haupt-DB wird NICHT verändert.")

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        match = connection.execute(
            """
            SELECT
                m.match_id,
                m.matchday,
                m.external_id,
                m.home_team_id,
                ht.name AS home_team,
                m.away_team_id,
                at.name AS away_team,
                m.home_goals,
                m.away_goals,
                m.status
            FROM matches AS m
            INNER JOIN teams AS ht
                ON ht.team_id = m.home_team_id
            INNER JOIN teams AS at
                ON at.team_id = m.away_team_id
            WHERE m.match_id = ?
            """,
            (MATCH_ID,),
        ).fetchone()

        if match is None:
            raise RuntimeError(
                f"Spiel {MATCH_ID} wurde nicht gefunden."
            )

        match = dict(match)

        print_rows(
            "MATCH",
            [match],
        )

        events = rows(
            connection,
            """
            SELECT
                e.event_id,
                et.code,
                e.minute,
                e.second,
                e.team_id,
                t.name AS team_name,
                e.player_id,
                p.first_name,
                p.last_name,
                e.related_player_id,
                rp.first_name AS related_first_name,
                rp.last_name AS related_last_name,
                e.value,
                e.notes,
                e.external_id
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            LEFT JOIN teams AS t
                ON t.team_id = e.team_id
            LEFT JOIN players AS p
                ON p.player_id = e.player_id
            LEFT JOIN players AS rp
                ON rp.player_id = e.related_player_id
            WHERE e.match_id = ?
            ORDER BY
                CASE
                    WHEN e.minute IS NULL THEN 999
                    ELSE e.minute
                END,
                COALESCE(e.second, 0),
                e.event_id
            """,
            (MATCH_ID,),
        )

        print_rows(
            "ALLE EVENTS",
            events,
        )

        goal_codes = (
            "GOAL",
            "OWN_GOAL",
            "PENALTY_GOAL",
        )

        goal_events = [
            event
            for event in events
            if event["code"] in goal_codes
        ]

        print_rows(
            "TOR-EVENTS",
            goal_events,
        )

        score_home = int(
            match["home_goals"] or 0
        )
        score_away = int(
            match["away_goals"] or 0
        )

        event_home = 0
        event_away = 0

        for event in goal_events:
            team_id = event["team_id"]
            code = event["code"]

            if code == "OWN_GOAL":
                if team_id == match["home_team_id"]:
                    event_away += 1
                elif team_id == match["away_team_id"]:
                    event_home += 1
                continue

            if team_id == match["home_team_id"]:
                event_home += 1
            elif team_id == match["away_team_id"]:
                event_away += 1

        print()
        print("=" * 110)
        print("ERGEBNIS VS. TOR-EVENTS")
        print("=" * 110)
        print(
            f"Endergebnis: "
            f"{match['home_team']} "
            f"{score_home}:{score_away} "
            f"{match['away_team']}"
        )
        print(
            f"Aus Events:  "
            f"{match['home_team']} "
            f"{event_home}:{event_away} "
            f"{match['away_team']}"
        )
        print(
            f"Ergebnis-Tore gesamt: "
            f"{score_home + score_away}"
        )
        print(
            f"Tor-Events gesamt:     "
            f"{len(goal_events)}"
        )

        event_type_counts = rows(
            connection,
            """
            SELECT
                et.code,
                COUNT(*) AS count
            FROM events AS e
            INNER JOIN event_types AS et
                ON et.event_type_id = e.event_type_id
            WHERE e.match_id = ?
            GROUP BY et.code
            ORDER BY et.code
            """,
            (MATCH_ID,),
        )

        print_rows(
            "EVENTTYPEN",
            event_type_counts,
        )

        print()
        print("=" * 110)
        print("BEFUND")
        print("=" * 110)

        missing = (
            score_home
            + score_away
            - len(goal_events)
        )

        if missing == 0:
            print(
                "Keine Toranzahl-Abweichung vorhanden."
            )
        elif missing > 0:
            print(
                f"Es fehlen {missing} Tor-Event(s) "
                f"gegenüber dem Endergebnis."
            )

            if event_home != score_home:
                print(
                    f"Heimteam-Abweichung: "
                    f"Ergebnis={score_home}, "
                    f"Events={event_home}"
                )

            if event_away != score_away:
                print(
                    f"Auswärtsteam-Abweichung: "
                    f"Ergebnis={score_away}, "
                    f"Events={event_away}"
                )

            print(
                "Noch KEINE Datenänderung. "
                "Als Nächstes prüfen wir für genau dieses "
                "Spiel Roh-HTML/Liveticker gegen die DB."
            )
        else:
            print(
                "Es existieren mehr Tor-Events als "
                "Tore im Endergebnis."
            )
            print(
                "Noch KEINE Datenänderung."
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
