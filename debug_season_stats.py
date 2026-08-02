import sqlite3


DATABASE_PATH = (
    "data/database/kreisligamanager_test.db"
)


def main() -> None:
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    print("=" * 70)
    print("EVENTTYPEN")
    print("=" * 70)

    cursor.execute(
        """
        SELECT
            event_types.code,
            COUNT(*)
        FROM events
        INNER JOIN event_types
            ON event_types.event_type_id =
                events.event_type_id
        GROUP BY event_types.code
        ORDER BY event_types.code;
        """
    )

    for row in cursor.fetchall():
        print(row)

    print()
    print("=" * 70)
    print("SPIELE MIT ABWEICHENDER TORANZAHL")
    print("=" * 70)

    cursor.execute(
    """
    SELECT
        matches.match_id,
        home_teams.name AS home_team,
        away_teams.name AS away_team,
        COALESCE(matches.home_goals, 0)
            + COALESCE(matches.away_goals, 0)
            AS match_goals,
        SUM(
            CASE
                WHEN event_types.code IN (
                    'GOAL',
                    'PENALTY_GOAL',
                    'OWN_GOAL'
                )
                THEN 1
                ELSE 0
            END
        ) AS event_goals
    FROM matches
    INNER JOIN teams AS home_teams
        ON home_teams.team_id =
            matches.home_team_id
    INNER JOIN teams AS away_teams
        ON away_teams.team_id =
            matches.away_team_id
    LEFT JOIN events
        ON events.match_id =
            matches.match_id
    LEFT JOIN event_types
        ON event_types.event_type_id =
            events.event_type_id
    GROUP BY
        matches.match_id,
        home_teams.name,
        away_teams.name,
        matches.home_goals,
        matches.away_goals
    HAVING match_goals != event_goals
    ORDER BY matches.match_id;
    """
)

    goal_mismatches = cursor.fetchall()

    print(
        "Anzahl:",
        len(goal_mismatches),
    )

    for row in goal_mismatches[:30]:
        print(row)

    print()
    print("=" * 70)
    print("MANNSCHAFTEN MIT FALSCHER MINUTENSUMME")
    print("=" * 70)

    cursor.execute(
        """
        SELECT
            player_match_stats.match_id,
            player_match_stats.team_id,
            SUM(
                player_match_stats.minutes_played
            ) AS total_minutes,
            SUM(
                player_match_stats.is_starting
            ) AS starters,
            SUM(
                player_match_stats.was_substituted_in
            ) AS substitutions_in,
            SUM(
                player_match_stats.was_substituted_out
            ) AS substitutions_out
        FROM player_match_stats
        GROUP BY
            player_match_stats.match_id,
            player_match_stats.team_id
        HAVING total_minutes != 990
        ORDER BY
            player_match_stats.match_id,
            player_match_stats.team_id;
        """
    )

    minute_mismatches = cursor.fetchall()

    print(
        "Anzahl:",
        len(minute_mismatches),
    )

    for row in minute_mismatches[:50]:
        print(row)

    connection.close()


if __name__ == "__main__":
    main()