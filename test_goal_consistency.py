from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")

GOAL_TYPES = (
    "GOAL",
    "PENALTY_GOAL",
    "OWN_GOAL",
)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT
                m.match_id,
                m.matchday,
                m.external_id,
                m.home_team_id,
                m.away_team_id,
                ht.name AS home_team,
                at.name AS away_team,
                m.home_goals,
                m.away_goals,

                SUM(
                    CASE
                        WHEN et.code IN (
                            'GOAL',
                            'PENALTY_GOAL',
                            'OWN_GOAL'
                        )
                        THEN 1
                        ELSE 0
                    END
                ) AS imported_goals_total,

                SUM(
                    CASE
                        WHEN et.code IN (
                            'GOAL',
                            'PENALTY_GOAL',
                            'OWN_GOAL'
                        )
                        AND e.team_id = m.home_team_id
                        THEN 1
                        ELSE 0
                    END
                ) AS imported_home_goals,

                SUM(
                    CASE
                        WHEN et.code IN (
                            'GOAL',
                            'PENALTY_GOAL',
                            'OWN_GOAL'
                        )
                        AND e.team_id = m.away_team_id
                        THEN 1
                        ELSE 0
                    END
                ) AS imported_away_goals,

                SUM(
                    CASE
                        WHEN et.code = 'GOAL'
                        THEN 1
                        ELSE 0
                    END
                ) AS normal_goals,

                SUM(
                    CASE
                        WHEN et.code = 'PENALTY_GOAL'
                        THEN 1
                        ELSE 0
                    END
                ) AS penalty_goals,

                SUM(
                    CASE
                        WHEN et.code = 'OWN_GOAL'
                        THEN 1
                        ELSE 0
                    END
                ) AS own_goals

            FROM matches AS m

            INNER JOIN teams AS ht
                ON ht.team_id = m.home_team_id

            INNER JOIN teams AS at
                ON at.team_id = m.away_team_id

            LEFT JOIN events AS e
                ON e.match_id = m.match_id

            LEFT JOIN event_types AS et
                ON et.event_type_id = e.event_type_id

            WHERE m.detail_imported = 1

            GROUP BY
                m.match_id,
                m.matchday,
                m.external_id,
                m.home_team_id,
                m.away_team_id,
                ht.name,
                at.name,
                m.home_goals,
                m.away_goals

            ORDER BY
                m.matchday,
                m.match_id
            """
        ).fetchall()

        print("=" * 72)
        print("TOR-KONSISTENZCHECK")
        print("=" * 72)

        if not rows:
            print("Keine detailimportierten Spiele gefunden.")
            return

        total_ok = 0
        team_ok = 0
        mismatches = 0

        for row in rows:
            expected_home = int(
                row["home_goals"] or 0
            )
            expected_away = int(
                row["away_goals"] or 0
            )
            expected_total = (
                expected_home
                + expected_away
            )

            imported_home = int(
                row["imported_home_goals"] or 0
            )
            imported_away = int(
                row["imported_away_goals"] or 0
            )
            imported_total = int(
                row["imported_goals_total"] or 0
            )

            total_matches = (
                expected_total
                == imported_total
            )

            team_matches = (
                expected_home == imported_home
                and expected_away == imported_away
            )

            if total_matches:
                total_ok += 1

            if team_matches:
                team_ok += 1

            if not team_matches:
                mismatches += 1

            status = (
                "OK"
                if team_matches
                else "ABWEICHUNG"
            )

            print()
            print(
                f"[{status}] "
                f"Spieltag {row['matchday']} | "
                f"{row['home_team']} - "
                f"{row['away_team']}"
            )

            print(
                "  Ergebnis: "
                f"{expected_home}:{expected_away}"
            )

            print(
                "  Import:   "
                f"{imported_home}:{imported_away}"
            )

            print(
                "  Events:   "
                f"GOAL={int(row['normal_goals'] or 0)}, "
                f"PENALTY_GOAL="
                f"{int(row['penalty_goals'] or 0)}, "
                f"OWN_GOAL="
                f"{int(row['own_goals'] or 0)}"
            )

            if (
                total_matches
                and not team_matches
            ):
                print(
                    "  Hinweis: Toranzahl stimmt insgesamt, "
                    "aber die Teamzuordnung ist falsch."
                )

            if not total_matches:
                print(
                    "  Hinweis: Auch die Gesamtzahl der "
                    "Tor-Events stimmt nicht."
                )

        print()
        print("=" * 72)
        print("ZUSAMMENFASSUNG")
        print("=" * 72)
        print(
            f"Detailspiele geprüft: {len(rows)}"
        )
        print(
            "Gesamttorzahl korrekt: "
            f"{total_ok}/{len(rows)}"
        )
        print(
            "Heim/Auswärts korrekt: "
            f"{team_ok}/{len(rows)}"
        )
        print(
            f"Abweichende Spiele: {mismatches}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
