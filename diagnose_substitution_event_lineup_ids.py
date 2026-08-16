from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")


def normalize_name(value: str) -> str:
    return " ".join(
        (value or "").split()
    ).casefold()


def main() -> None:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    print("=" * 120)
    print("DIAGNOSE WECHSEL-EVENTS: PLAYER_ID ↔ LINEUP")
    print("=" * 120)
    print(f"Datenbank: {DB_PATH}")
    print()

    rows = connection.execute(
        """
        SELECT
            e.event_id,
            e.match_id,
            e.team_id,
            e.player_id,
            e.related_player_id,
            e.minute,
            e.notes,
            e.value,
            et.code AS event_type,
            p.first_name,
            p.last_name,
            rp.first_name AS related_first_name,
            rp.last_name AS related_last_name,
            ht.name AS home_team,
            at.name AS away_team
        FROM events e
        INNER JOIN event_types et
            ON et.event_type_id = e.event_type_id
        INNER JOIN matches m
            ON m.match_id = e.match_id
        LEFT JOIN players p
            ON p.player_id = e.player_id
        LEFT JOIN players rp
            ON rp.player_id = e.related_player_id
        LEFT JOIN teams ht
            ON ht.team_id = m.home_team_id
        LEFT JOIN teams at
            ON at.team_id = m.away_team_id
        WHERE et.code IN (
            'SUBSTITUTION_IN',
            'SUBSTITUTION_OUT'
        )
        ORDER BY
            e.match_id,
            e.team_id,
            e.minute,
            e.event_id
        """
    ).fetchall()

    checked = 0
    missing_player = 0
    missing_related = 0

    for row in rows:
        checked += 1

        player_in_lineup = connection.execute(
            """
            SELECT 1
            FROM lineups
            WHERE
                match_id = ?
                AND team_id = ?
                AND player_id = ?
            LIMIT 1
            """,
            (
                row["match_id"],
                row["team_id"],
                row["player_id"],
            ),
        ).fetchone()

        related_in_lineup = None

        if row["related_player_id"] is not None:
            related_in_lineup = connection.execute(
                """
                SELECT 1
                FROM lineups
                WHERE
                    match_id = ?
                    AND team_id = ?
                    AND player_id = ?
                LIMIT 1
                """,
                (
                    row["match_id"],
                    row["team_id"],
                    row["related_player_id"],
                ),
            ).fetchone()

        if (
            player_in_lineup is not None
            and (
                row["related_player_id"] is None
                or related_in_lineup is not None
            )
        ):
            continue

        player_name = " ".join(
            part
            for part in (
                row["first_name"] or "",
                row["last_name"] or "",
            )
            if part
        ) or "-"

        related_name = " ".join(
            part
            for part in (
                row["related_first_name"] or "",
                row["related_last_name"] or "",
            )
            if part
        ) or "-"

        print("=" * 120)
        print(
            f"SPIEL {row['match_id']}: "
            f"{row['home_team'] or '?'} - "
            f"{row['away_team'] or '?'}"
        )
        print("-" * 120)
        print(
            f"{row['minute']}' | "
            f"{row['event_type']} | "
            f"team_id={row['team_id']} | "
            f"event_id={row['event_id']}"
        )
        print(
            f"player_id={row['player_id']} "
            f"({player_name}) | "
            f"im Lineup: "
            f"{'JA' if player_in_lineup is not None else 'NEIN'}"
        )
        print(
            f"related_player_id={row['related_player_id']} "
            f"({related_name}) | "
            f"im Lineup: "
            f"{'JA' if related_in_lineup is not None else 'NEIN'}"
        )

        if row["notes"]:
            print(f"Beschreibung: {row['notes']}")

        if row["value"]:
            print(f"value: {row['value']}")

        if player_in_lineup is None:
            missing_player += 1
            print()
            print("KANDIDATEN FÜR EVENT-SPIELER")
            print("-" * 120)

            target = normalize_name(player_name)

            lineup_rows = connection.execute(
                """
                SELECT
                    l.player_id,
                    p.first_name,
                    p.last_name,
                    p.external_id,
                    l.is_starting,
                    l.shirt_number
                FROM lineups l
                INNER JOIN players p
                    ON p.player_id = l.player_id
                WHERE
                    l.match_id = ?
                    AND l.team_id = ?
                ORDER BY
                    l.is_starting DESC,
                    l.player_id
                """,
                (
                    row["match_id"],
                    row["team_id"],
                ),
            ).fetchall()

            for lineup_row in lineup_rows:
                lineup_name = " ".join(
                    part
                    for part in (
                        lineup_row["first_name"] or "",
                        lineup_row["last_name"] or "",
                    )
                    if part
                )

                normalized_lineup = normalize_name(
                    lineup_name
                )

                if (
                    target
                    and normalized_lineup
                    and (
                        target == normalized_lineup
                        or target.startswith(
                            normalized_lineup + " "
                        )
                        or normalized_lineup.startswith(
                            target + " "
                        )
                    )
                ):
                    print(
                        f"  player_id={lineup_row['player_id']} | "
                        f"{lineup_name} | "
                        f"external_id={lineup_row['external_id']} | "
                        f"start={lineup_row['is_starting']} | "
                        f"Nr={lineup_row['shirt_number']}"
                    )

        if (
            row["related_player_id"] is not None
            and related_in_lineup is None
        ):
            missing_related += 1
            print()
            print("KANDIDATEN FÜR RELATED-SPIELER")
            print("-" * 120)

            target = normalize_name(
                related_name
            )

            lineup_rows = connection.execute(
                """
                SELECT
                    l.player_id,
                    p.first_name,
                    p.last_name,
                    p.external_id,
                    l.is_starting,
                    l.shirt_number
                FROM lineups l
                INNER JOIN players p
                    ON p.player_id = l.player_id
                WHERE
                    l.match_id = ?
                    AND l.team_id = ?
                ORDER BY
                    l.is_starting DESC,
                    l.player_id
                """,
                (
                    row["match_id"],
                    row["team_id"],
                ),
            ).fetchall()

            for lineup_row in lineup_rows:
                lineup_name = " ".join(
                    part
                    for part in (
                        lineup_row["first_name"] or "",
                        lineup_row["last_name"] or "",
                    )
                    if part
                )

                normalized_lineup = normalize_name(
                    lineup_name
                )

                if (
                    target
                    and normalized_lineup
                    and (
                        target == normalized_lineup
                        or target.startswith(
                            normalized_lineup + " "
                        )
                        or normalized_lineup.startswith(
                            target + " "
                        )
                    )
                ):
                    print(
                        f"  player_id={lineup_row['player_id']} | "
                        f"{lineup_name} | "
                        f"external_id={lineup_row['external_id']} | "
                        f"start={lineup_row['is_starting']} | "
                        f"Nr={lineup_row['shirt_number']}"
                    )

        print()

    print("=" * 120)
    print("ZUSAMMENFASSUNG")
    print("=" * 120)
    print(
        f"Wechsel-Events geprüft:           {checked}"
    )
    print(
        f"Event-player_id nicht im Lineup:  {missing_player}"
    )
    print(
        f"Related-player_id nicht im Lineup:{missing_related}"
    )

    if (
        missing_player == 0
        and missing_related == 0
    ):
        print()
        print(
            "ERGEBNIS: Alle Wechsel-Event-Spieler "
            "existieren im jeweiligen Lineup."
        )
    else:
        print()
        print(
            "ERGEBNIS: Es gibt Wechsel-Events mit "
            "Spieler-IDs außerhalb des Lineups."
        )

    print("=" * 120)

    connection.close()


if __name__ == "__main__":
    main()
