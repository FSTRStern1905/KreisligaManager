from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/database/kreisligamanager.db")
MATCH_EXTERNAL_ID = "02TKDR1R3C000000VS5489BUVUD1610F"


def sep(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def main() -> None:
    sep("PLAYER_MATCH_STATS DIAGNOSE – SPIEL 3")

    if not DATABASE_PATH.exists():
        print("Datenbank nicht gefunden.")
        return

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        match = connection.execute(
            """
            SELECT
                m.match_id,
                ht.name,
                at.name,
                m.home_goals,
                m.away_goals
            FROM matches m
            INNER JOIN teams ht
                ON ht.team_id = m.home_team_id
            INNER JOIN teams at
                ON at.team_id = m.away_team_id
            WHERE m.external_id = ?
            LIMIT 1;
            """,
            (MATCH_EXTERNAL_ID,),
        ).fetchone()

        if match is None:
            print(
                "Spiel nicht in der Datenbank. "
                "Bitte zuerst den 5-Spiele-Test erneut "
                "erfolgreich importieren."
            )
            return

        match_id, home_team, away_team, home_goals, away_goals = match

        print(
            f"Spiel {match_id}: {home_team} - {away_team} "
            f"{home_goals}:{away_goals}"
        )

        sep("TOR-EVENTS")

        goal_events = connection.execute(
            """
            SELECT
                e.event_id,
                et.code,
                e.minute,
                e.player_id,
                p.first_name,
                p.last_name,
                p.external_id,
                t.name,
                pms.player_match_stat_id,
                pms.goals,
                pms.own_goals
            FROM events e
            INNER JOIN event_types et
                ON et.event_type_id = e.event_type_id
            LEFT JOIN players p
                ON p.player_id = e.player_id
            LEFT JOIN teams t
                ON t.team_id = e.team_id
            LEFT JOIN player_match_stats pms
                ON pms.match_id = e.match_id
                AND pms.player_id = e.player_id
            WHERE
                e.match_id = ?
                AND et.code IN (
                    'GOAL',
                    'PENALTY_GOAL',
                    'OWN_GOAL'
                )
            ORDER BY
                e.minute,
                e.event_id;
            """,
            (match_id,),
        ).fetchall()

        for row in goal_events:
            (
                event_id,
                code,
                minute,
                player_id,
                first_name,
                last_name,
                external_id,
                team_name,
                stat_id,
                goals,
                own_goals,
            ) = row

            player_name = " ".join(
                part
                for part in (
                    first_name or "",
                    last_name or "",
                )
                if part
            )

            print(
                f"{minute}'. {code:<13} "
                f"{player_name:<30} "
                f"| player_id={player_id} "
                f"| external_id={external_id or '-'}"
            )
            print(
                f"    Team={team_name} "
                f"| Event-ID={event_id} "
                f"| Stat-ID={stat_id} "
                f"| Stats Tore={goals} "
                f"| Stats ET={own_goals}"
            )

            if stat_id is None:
                print(
                    "    >>> FEHLER: "
                    "Keine player_match_stats-Zeile "
                    "für diesen Event-Spieler."
                )

        sep("PLAYER_MATCH_STATS MIT TOREN")

        stats = connection.execute(
            """
            SELECT
                pms.player_match_stat_id,
                pms.player_id,
                p.first_name,
                p.last_name,
                p.external_id,
                t.name,
                pms.goals,
                pms.own_goals,
                pms.minutes_played,
                pms.is_starting,
                pms.was_substituted_in,
                pms.was_substituted_out
            FROM player_match_stats pms
            INNER JOIN players p
                ON p.player_id = pms.player_id
            LEFT JOIN teams t
                ON t.team_id = pms.team_id
            WHERE
                pms.match_id = ?
                AND (
                    pms.goals > 0
                    OR pms.own_goals > 0
                )
            ORDER BY
                t.name,
                p.last_name,
                p.first_name;
            """,
            (match_id,),
        ).fetchall()

        for row in stats:
            (
                stat_id,
                player_id,
                first_name,
                last_name,
                external_id,
                team_name,
                goals,
                own_goals,
                minutes_played,
                is_starting,
                sub_in,
                sub_out,
            ) = row

            player_name = " ".join(
                part
                for part in (
                    first_name or "",
                    last_name or "",
                )
                if part
            )

            print(
                f"{player_name:<30} "
                f"| player_id={player_id} "
                f"| external_id={external_id or '-'}"
            )
            print(
                f"    Team={team_name} "
                f"| Tore={goals} "
                f"| ET={own_goals} "
                f"| Minuten={minutes_played} "
                f"| Start={is_starting} "
                f"| Ein={sub_in} "
                f"| Aus={sub_out} "
                f"| Stat-ID={stat_id}"
            )

        sep("ZUSAMMENFASSUNG")

        event_goals = sum(
            1
            for row in goal_events
            if row[3] is not None
        )

        stat_goals = connection.execute(
            """
            SELECT
                COALESCE(
                    SUM(goals + own_goals),
                    0
                )
            FROM player_match_stats
            WHERE match_id = ?;
            """,
            (match_id,),
        ).fetchone()[0]

        unmapped = [
            row
            for row in goal_events
            if (
                row[3] is not None
                and row[8] is None
            )
        ]

        print(
            f"Tor-Events mit Spieler:   {event_goals}"
        )
        print(
            f"player_match_stats Tore:  {stat_goals}"
        )
        print(
            f"Tor-Spieler ohne Stats:   {len(unmapped)}"
        )

        if unmapped:
            print()
            print(
                ">>> Der Fehler liegt sehr wahrscheinlich "
                "bei der Spielerzuordnung zwischen "
                "Events/Aufstellung und PlayerMatchStats."
            )
        else:
            print()
            print(
                ">>> Alle Event-Spieler besitzen Stats. "
                "Dann liegt der Fehler in der "
                "Zählerlogik des PlayerMatchStatsBuilder."
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
