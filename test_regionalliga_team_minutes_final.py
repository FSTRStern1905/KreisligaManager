from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(
    "data/database/regionalliga_suedwest_2526_final_test.db"
)

COMPETITION_NAME = "Regionalliga Südwest"


def separator(title: str) -> None:
    print()
    print("=" * 110)
    print(title)
    print("=" * 110)


def get_competition_id(
    connection: sqlite3.Connection,
) -> int:
    row = connection.execute(
        """
        SELECT competition_id
        FROM competitions
        WHERE name = ?
        ORDER BY competition_id DESC
        LIMIT 1
        """,
        (COMPETITION_NAME,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Wettbewerb nicht gefunden: {COMPETITION_NAME}"
        )

    return int(
        row["competition_id"]
    )


def get_minute_cases(
    connection: sqlite3.Connection,
    competition_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            m.match_id,
            m.matchday,
            m.external_id,
            ht.name AS home_team,
            at.name AS away_team,
            pms.team_id,
            t.name AS team_name,
            COUNT(*) AS squad_size,
            SUM(
                CASE
                    WHEN pms.is_starting = 1
                    THEN 1
                    ELSE 0
                END
            ) AS starters,
            SUM(
                COALESCE(
                    pms.minutes_played,
                    0
                )
            ) AS team_minutes
        FROM player_match_stats AS pms
        INNER JOIN matches AS m
            ON m.match_id = pms.match_id
        INNER JOIN teams AS t
            ON t.team_id = pms.team_id
        INNER JOIN teams AS ht
            ON ht.team_id = m.home_team_id
        INNER JOIN teams AS at
            ON at.team_id = m.away_team_id
        WHERE m.competition_id = ?
        GROUP BY
            m.match_id,
            m.matchday,
            m.external_id,
            ht.name,
            at.name,
            pms.team_id,
            t.name
        HAVING
            starters != 11
            OR team_minutes != 990
        ORDER BY
            m.matchday,
            m.match_id,
            pms.team_id
        """,
        (competition_id,),
    ).fetchall()


def get_team_events(
    connection: sqlite3.Connection,
    match_id: int,
    team_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            e.event_id,
            et.code,
            e.minute,
            e.second,
            e.team_id,
            e.player_id,
            p.first_name,
            p.last_name,
            e.related_player_id,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name,
            e.value,
            e.notes
        FROM events AS e
        INNER JOIN event_types AS et
            ON et.event_type_id = e.event_type_id
        LEFT JOIN players AS p
            ON p.player_id = e.player_id
        LEFT JOIN players AS rp
            ON rp.player_id = e.related_player_id
        WHERE
            e.match_id = ?
            AND (
                e.team_id = ?
                OR (
                    e.team_id IS NULL
                    AND et.code IN (
                        'RED_CARD',
                        'YELLOW_RED_CARD'
                    )
                )
            )
        ORDER BY
            CASE
                WHEN e.minute IS NULL THEN 999
                ELSE e.minute
            END,
            COALESCE(e.second, 0),
            e.event_id
        """,
        (
            match_id,
            team_id,
        ),
    ).fetchall()


def get_stats(
    connection: sqlite3.Connection,
    match_id: int,
    team_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pms.player_id,
            p.first_name,
            p.last_name,
            pms.is_starting,
            pms.was_substituted_in,
            pms.was_substituted_out,
            pms.minute_in,
            pms.minute_out,
            pms.minutes_played
        FROM player_match_stats AS pms
        LEFT JOIN players AS p
            ON p.player_id = pms.player_id
        WHERE
            pms.match_id = ?
            AND pms.team_id = ?
        ORDER BY
            pms.is_starting DESC,
            pms.minutes_played DESC,
            p.last_name,
            p.first_name
        """,
        (
            match_id,
            team_id,
        ),
    ).fetchall()


def player_name(
    first_name: str | None,
    last_name: str | None,
) -> str:
    return " ".join(
        part.strip()
        for part in (
            first_name or "",
            last_name or "",
        )
        if part.strip()
    ) or "?"


def classify_case(
    team_minutes: int,
    starters: int,
    events: list[sqlite3.Row],
) -> tuple[str, str]:
    substitution_events = [
        row
        for row in events
        if row["code"] in (
            "SUBSTITUTION_IN",
            "SUBSTITUTION_OUT",
        )
    ]

    unknown_sub_minutes = [
        row
        for row in substitution_events
        if (
            row["minute"] is None
            or int(row["minute"] or 0) <= 0
        )
    ]

    late_substitutions = [
        row
        for row in substitution_events
        if (
            row["minute"] is not None
            and int(row["minute"]) > 90
        )
    ]

    red_cards = [
        row
        for row in events
        if row["code"] in (
            "RED_CARD",
            "YELLOW_RED_CARD",
        )
    ]

    substitution_in = sum(
        1
        for row in substitution_events
        if row["code"] == "SUBSTITUTION_IN"
    )

    substitution_out = sum(
        1
        for row in substitution_events
        if row["code"] == "SUBSTITUTION_OUT"
    )

    if starters != 11:
        return (
            "TECHNISCH",
            f"Startelf-Anzahl ist {starters} statt 11.",
        )

    if unknown_sub_minutes:
        return (
            "QUELLE_WECHSELMINUTE",
            (
                f"{len(unknown_sub_minutes)} Wechsel-Event(s) "
                "mit Minute 0/NULL."
            ),
        )

    if red_cards:
        return (
            "PLATZVERWEIS",
            (
                f"{len(red_cards)} Platzverweis-Event(s) vorhanden."
            ),
        )

    if late_substitutions:
        return (
            "NACHSPIELZEIT",
            (
                f"{len(late_substitutions)} Wechsel-Event(s) "
                "nach Minute 90."
            ),
        )

    if substitution_in != substitution_out:
        return (
            "QUELLE_WECHSELKETTE",
            (
                f"Wechselkette unausgeglichen: "
                f"IN={substitution_in}, OUT={substitution_out}."
            ),
        )

    if team_minutes != 990:
        return (
            "TECHNISCH",
            (
                f"Team-Minuten={team_minutes}, "
                "aber kein bekannter Sonderfall erkannt."
            ),
        )

    return (
        "OK",
        "Keine Abweichung.",
    )


def main() -> None:
    print("=" * 110)
    print(
        "REGIONALLIGA SÜDWEST 2025/26 "
        "- FINALER TEAM-MINUTEN-QUALITÄTSTEST"
    )
    print("=" * 110)
    print(f"Datenbank: {DB_PATH}")
    print("Haupt-DB wird NICHT verändert.")
    print(
        "Rück-/Mehrfachwechsel werden NICHT geprüft, "
        "da sie in der Regionalliga nicht zulässig/relevant sind."
    )

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        competition_id = get_competition_id(
            connection
        )

        cases = get_minute_cases(
            connection,
            competition_id,
        )

        print(
            f"Abweichende Spiel/Team-Fälle: "
            f"{len(cases)}"
        )

        groups: dict[str, list[dict]] = {
            "QUELLE_WECHSELMINUTE": [],
            "PLATZVERWEIS": [],
            "NACHSPIELZEIT": [],
            "QUELLE_WECHSELKETTE": [],
            "TECHNISCH": [],
            "OK": [],
        }

        for case in cases:
            match_id = int(
                case["match_id"]
            )
            team_id = int(
                case["team_id"]
            )
            team_minutes = int(
                case["team_minutes"] or 0
            )
            starters = int(
                case["starters"] or 0
            )

            events = get_team_events(
                connection,
                match_id,
                team_id,
            )

            stats = get_stats(
                connection,
                match_id,
                team_id,
            )

            category, reason = classify_case(
                team_minutes=team_minutes,
                starters=starters,
                events=events,
            )

            groups[category].append(
                {
                    "case": case,
                    "events": events,
                    "stats": stats,
                    "reason": reason,
                }
            )

        group_titles = (
            (
                "QUELLE_WECHSELMINUTE",
                "GRUPPE A - QUELLSEITIG UNBEKANNTE WECHSELMINUTEN",
            ),
            (
                "PLATZVERWEIS",
                "GRUPPE B - PLATZVERWEIS / ERKLÄRTE ABWEICHUNG",
            ),
            (
                "NACHSPIELZEIT",
                "GRUPPE C - NACHSPIELZEIT / WECHSEL > 90'",
            ),
            (
                "QUELLE_WECHSELKETTE",
                "GRUPPE D - QUELLSEITIG UNVOLLSTÄNDIGE WECHSELKETTE",
            ),
            (
                "TECHNISCH",
                "GRUPPE E - ECHTE TECHNISCHE AUFFÄLLIGKEIT",
            ),
        )

        for group_key, title in group_titles:
            separator(title)

            items = groups[group_key]

            if not items:
                print("(keine)")
                continue

            for item in items:
                case = item["case"]
                events = item["events"]
                stats = item["stats"]
                reason = item["reason"]

                print()
                print(
                    f"Spiel {case['match_id']} | "
                    f"ST {case['matchday']} | "
                    f"{case['home_team']} - "
                    f"{case['away_team']}"
                )
                print(
                    f"Team:    {case['team_name']}"
                )
                print(
                    f"Starter: {case['starters']} | "
                    f"Kader: {case['squad_size']} | "
                    f"Minuten: {case['team_minutes']}"
                )
                print(
                    f"Grund:   {reason}"
                )

                relevant_events = [
                    row
                    for row in events
                    if row["code"] in (
                        "SUBSTITUTION_IN",
                        "SUBSTITUTION_OUT",
                        "RED_CARD",
                        "YELLOW_RED_CARD",
                    )
                ]

                if relevant_events:
                    print("EVENTS")
                    print("-" * 110)

                    for row in relevant_events:
                        minute = (
                            "?"
                            if row["minute"] is None
                            else str(row["minute"])
                        )

                        name = player_name(
                            row["first_name"],
                            row["last_name"],
                        )
                        related = player_name(
                            row["related_first_name"],
                            row["related_last_name"],
                        )

                        print(
                            f"  {minute:>3}' "
                            f"{row['code']:<20} "
                            f"{name} ↔ {related} | "
                            f"{row['value'] or ''}"
                        )

                if group_key == "TECHNISCH":
                    print("PLAYER-STATS")
                    print("-" * 110)

                    for row in stats:
                        print(
                            f"  "
                            f"{player_name(row['first_name'], row['last_name'])} | "
                            f"Start={row['is_starting']} | "
                            f"IN={row['was_substituted_in']} | "
                            f"OUT={row['was_substituted_out']} | "
                            f"minute_in={row['minute_in']} | "
                            f"minute_out={row['minute_out']} | "
                            f"minutes={row['minutes_played']}"
                        )

        separator("GESAMTERGEBNIS")

        print(
            f"Gruppe A - Wechselminute unbekannt: "
            f"{len(groups['QUELLE_WECHSELMINUTE'])}"
        )
        print(
            f"Gruppe B - Platzverweis:            "
            f"{len(groups['PLATZVERWEIS'])}"
        )
        print(
            f"Gruppe C - Nachspielzeit:           "
            f"{len(groups['NACHSPIELZEIT'])}"
        )
        print(
            f"Gruppe D - Wechselkette Quelle:     "
            f"{len(groups['QUELLE_WECHSELKETTE'])}"
        )
        print(
            f"Gruppe E - technische Fehler:       "
            f"{len(groups['TECHNISCH'])}"
        )

        technical_errors = len(
            groups["TECHNISCH"]
        )

        print()

        if technical_errors == 0:
            print(
                "STATUS: OK - keine echten technischen "
                "Team-Minutenfehler."
            )
            print(
                "Verbleibende Abweichungen sind durch "
                "Quelle oder reguläre Sonderfälle erklärt."
            )
        else:
            print(
                "STATUS: PRÜFEN - technische "
                f"Team-Minutenfälle: {technical_errors}"
            )

        print("=" * 110)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
