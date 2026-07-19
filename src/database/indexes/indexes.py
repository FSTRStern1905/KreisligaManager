import sqlite3


class DatabaseIndexes:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        indexes = [
            """
            CREATE INDEX IF NOT EXISTS
                idx_competitions_league_id
            ON competitions(league_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_competitions_season_id
            ON competitions(season_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_competition_teams_competition_id
            ON competition_teams(competition_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_competition_teams_team_id
            ON competition_teams(team_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_teams_club_id
            ON teams(club_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_players_team_id
            ON players(team_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_matches_competition_id
            ON matches(competition_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_matches_season_id
            ON matches(season_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_matches_league_id
            ON matches(league_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_matches_home_team_id
            ON matches(home_team_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_matches_away_team_id
            ON matches(away_team_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_events_match_id
            ON events(match_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_events_player_id
            ON events(player_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_events_team_id
            ON events(team_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_lineups_match_id
            ON lineups(match_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS
                idx_lineups_player_id
            ON lineups(player_id);
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_clubs_external_id
            ON clubs(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_leagues_external_id
            ON leagues(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_seasons_external_id
            ON seasons(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_teams_external_id
            ON teams(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_players_external_id
            ON players(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_matches_external_id
            ON matches(external_id)
            WHERE external_id IS NOT NULL;
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_events_external_id
            ON events(external_id)
            WHERE external_id IS NOT NULL;
            """,
        ]

        for index in indexes:
            self.cursor.execute(index)