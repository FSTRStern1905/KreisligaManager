from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path("data/database/kreisligamanager.db")
COMPETITION_NAME = "Bundesliga"


def normalize(value: str | None) -> str:
    return " ".join(
        (value or "").casefold().split()
    )


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Datenbank nicht gefunden: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        competition = connection.execute(
            """
            SELECT
                competition_id,
                name
            FROM competitions
            WHERE name = ?
            LIMIT 1
            """,
            (COMPETITION_NAME,),
        ).fetchone()

        if competition is None:
            raise RuntimeError(
                f"Wettbewerb nicht gefunden: "
                f"{COMPETITION_NAME}"
            )

        competition_id = int(
            competition["competition_id"]
        )

        print("=" * 92)
        print("WECHSEL-ALIAS-PROJEKTION")
        print("=" * 92)
        print(
            f"Wettbewerb: {competition['name']} "
            f"(competition_id={competition_id})"
        )

        matches = connection.execute(
            """
            SELECT
                match_id,
                matchday,
                home_team_id,
                away_team_id
            FROM matches
            WHERE
                competition_id = ?
                AND detail_imported = 1
            ORDER BY
                matchday,
                match_id
            """,
            (competition_id,),
        ).fetchall()

        total_team_matches = 0
        currently_matching = 0
        projected_matching = 0

        direct_event_players = 0
        alias_event_players = 0
        unresolved_event_players = 0
        ambiguous_event_players = 0

        unresolved_examples: list[dict] = []
        ambiguous_examples: list[dict] = []

        for match in matches:
            match_id = int(
                match["match_id"]
            )

            for team_id in (
                int(match["home_team_id"]),
                int(match["away_team_id"]),
            ):
                total_team_matches += 1

                event_rows = connection.execute(
                    """
                    SELECT
                        e.event_id,
                        e.player_id,
                        et.code AS event_type,
                        p.first_name,
                        p.last_name
                    FROM events AS e
                    INNER JOIN event_types AS et
                        ON et.event_type_id =
                           e.event_type_id
                    LEFT JOIN players AS p
                        ON p.player_id =
                           e.player_id
                    WHERE
                        e.match_id = ?
                        AND e.team_id = ?
                        AND et.code IN (
                            'SUBSTITUTION_IN',
                            'SUBSTITUTION_OUT'
                        )
                    ORDER BY
                        e.event_id
                    """,
                    (
                        match_id,
                        team_id,
                    ),
                ).fetchall()

                event_in = sum(
                    1
                    for row in event_rows
                    if row["event_type"]
                    == "SUBSTITUTION_IN"
                )
                event_out = sum(
                    1
                    for row in event_rows
                    if row["event_type"]
                    == "SUBSTITUTION_OUT"
                )

                stats = connection.execute(
                    """
                    SELECT
                        SUM(
                            CASE
                                WHEN was_substituted_in = 1
                                THEN 1
                                ELSE 0
                            END
                        ) AS in_count,
                        SUM(
                            CASE
                                WHEN was_substituted_out = 1
                                THEN 1
                                ELSE 0
                            END
                        ) AS out_count
                    FROM player_match_stats
                    WHERE
                        match_id = ?
                        AND team_id = ?
                    """,
                    (
                        match_id,
                        team_id,
                    ),
                ).fetchone()

                stats_in = int(
                    stats["in_count"] or 0
                )
                stats_out = int(
                    stats["out_count"] or 0
                )

                if (
                    stats_in == event_in
                    and stats_out == event_out
                ):
                    currently_matching += 1

                projected_in_players: set[int] = set()
                projected_out_players: set[int] = set()

                for event in event_rows:
                    if event["player_id"] is None:
                        unresolved_event_players += 1
                        continue

                    event_player_id = int(
                        event["player_id"]
                    )

                    direct_lineup = connection.execute(
                        """
                        SELECT
                            player_id
                        FROM lineups
                        WHERE
                            match_id = ?
                            AND team_id = ?
                            AND player_id = ?
                        LIMIT 1
                        """,
                        (
                            match_id,
                            team_id,
                            event_player_id,
                        ),
                    ).fetchone()

                    mapped_player_id: int | None = None

                    if direct_lineup is not None:
                        mapped_player_id = event_player_id
                        direct_event_players += 1
                    else:
                        first_name = str(
                            event["first_name"] or ""
                        )
                        last_name = str(
                            event["last_name"] or ""
                        )

                        candidates = connection.execute(
                            """
                            SELECT
                                l.player_id,
                                p.first_name,
                                p.last_name
                            FROM lineups AS l
                            INNER JOIN players AS p
                                ON p.player_id =
                                   l.player_id
                            WHERE
                                l.match_id = ?
                                AND l.team_id = ?
                            """,
                            (
                                match_id,
                                team_id,
                            ),
                        ).fetchall()

                        exact = [
                            row
                            for row in candidates
                            if (
                                normalize(
                                    row["first_name"]
                                )
                                == normalize(first_name)
                                and normalize(
                                    row["last_name"]
                                )
                                == normalize(last_name)
                            )
                        ]

                        if len(exact) == 1:
                            mapped_player_id = int(
                                exact[0]["player_id"]
                            )
                            alias_event_players += 1
                        elif len(exact) > 1:
                            ambiguous_event_players += 1

                            if len(
                                ambiguous_examples
                            ) < 20:
                                ambiguous_examples.append(
                                    {
                                        "match_id": match_id,
                                        "matchday": match[
                                            "matchday"
                                        ],
                                        "team_id": team_id,
                                        "name": (
                                            f"{first_name} "
                                            f"{last_name}"
                                        ).strip(),
                                        "event_type": event[
                                            "event_type"
                                        ],
                                        "matches": len(exact),
                                    }
                                )
                        else:
                            unresolved_event_players += 1

                            if len(
                                unresolved_examples
                            ) < 30:
                                unresolved_examples.append(
                                    {
                                        "match_id": match_id,
                                        "matchday": match[
                                            "matchday"
                                        ],
                                        "team_id": team_id,
                                        "name": (
                                            f"{first_name} "
                                            f"{last_name}"
                                        ).strip(),
                                        "event_type": event[
                                            "event_type"
                                        ],
                                    }
                                )

                    if mapped_player_id is None:
                        continue

                    if (
                        event["event_type"]
                        == "SUBSTITUTION_IN"
                    ):
                        projected_in_players.add(
                            mapped_player_id
                        )
                    else:
                        projected_out_players.add(
                            mapped_player_id
                        )

                projected_in = len(
                    projected_in_players
                )
                projected_out = len(
                    projected_out_players
                )

                if (
                    projected_in == event_in
                    and projected_out == event_out
                ):
                    projected_matching += 1

        print()
        print("ERGEBNIS")
        print("-" * 92)
        print(
            f"Spiel/Team-Kombinationen:          "
            f"{total_team_matches}"
        )
        print(
            f"Aktuell Stats = Events:            "
            f"{currently_matching}/"
            f"{total_team_matches}"
        )
        print(
            f"Nach Alias-Fix projiziert:          "
            f"{projected_matching}/"
            f"{total_team_matches}"
        )
        print(
            f"Verbesserung:                       "
            f"+{projected_matching - currently_matching}"
        )

        print()
        print("EVENT-SPIELER-MAPPING")
        print("-" * 92)
        print(
            f"Direkt im Lineup gefunden:          "
            f"{direct_event_players}"
        )
        print(
            f"Per eindeutigem Namensalias lösbar: "
            f"{alias_event_players}"
        )
        print(
            f"Nicht im Lineup vorhanden:          "
            f"{unresolved_event_players}"
        )
        print(
            f"Mehrdeutige Namenszuordnung:        "
            f"{ambiguous_event_players}"
        )

        if unresolved_examples:
            print()
            print("BEISPIELE ECHTER QUELLENLÜCKEN")
            print("-" * 92)

            for item in unresolved_examples:
                print(
                    f"ST {item['matchday']} | "
                    f"Spiel {item['match_id']} | "
                    f"team_id={item['team_id']} | "
                    f"{item['event_type']} | "
                    f"{item['name'] or '?'}"
                )

        if ambiguous_examples:
            print()
            print("BEISPIELE MEHRDEUTIG")
            print("-" * 92)

            for item in ambiguous_examples:
                print(
                    f"ST {item['matchday']} | "
                    f"Spiel {item['match_id']} | "
                    f"team_id={item['team_id']} | "
                    f"{item['event_type']} | "
                    f"{item['name'] or '?'} | "
                    f"Treffer={item['matches']}"
                )

        print()
        print("=" * 92)
        print("PROJEKTION ENDE")
        print("=" * 92)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
