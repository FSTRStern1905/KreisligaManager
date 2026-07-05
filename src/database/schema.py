import sqlite3


class DatabaseSchema:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def create_all_tables(self):
        self.enable_foreign_keys()

        self.create_countries_table()
        self.create_associations_table()
        self.create_seasons_table()
        self.create_leagues_table()
        self.create_clubs_table()
        self.create_teams_table()
        self.create_players_table()
        self.create_stadiums_table()
        self.create_referees_table()
        self.create_event_types_table()
        self.create_matches_table()
        self.create_lineups_table()
        self.create_events_table()
        self.create_formations_table()
        self.create_match_formations_table()
        self.create_staff_table()
        self.create_weather_table()

        self.create_indexes()
        self.insert_default_event_types()

        self.connection.commit()

    def enable_foreign_keys(self):
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def create_countries_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                country_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                iso_code TEXT
            );
        """)

    def create_associations_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS associations (
                association_id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                short_name TEXT,
                FOREIGN KEY (country_id) REFERENCES countries(country_id)
            );
        """)

    def create_seasons_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_date TEXT,
                end_date TEXT
            );
        """)

    def create_leagues_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS leagues (
                league_id INTEGER PRIMARY KEY AUTOINCREMENT,
                association_id INTEGER,
                name TEXT NOT NULL,
                level INTEGER,
                season_type TEXT,
                FOREIGN KEY (association_id) REFERENCES associations(association_id)
            );
        """)

    def create_clubs_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clubs (
                club_id INTEGER PRIMARY KEY AUTOINCREMENT,
                association_id INTEGER,
                name TEXT NOT NULL UNIQUE,
                short_name TEXT,
                city TEXT,
                FOREIGN KEY (association_id) REFERENCES associations(association_id)
            );
        """)

    def create_teams_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                short_name TEXT,
                team_number INTEGER,
                FOREIGN KEY (club_id) REFERENCES clubs(club_id)
            );
        """)

    def create_players_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT NOT NULL,
                birthdate TEXT,
                position TEXT,
                foot TEXT,
                is_active INTEGER DEFAULT 1
            );
        """)

    def create_stadiums_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stadiums (
                stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                capacity INTEGER
            );
        """)

    def create_referees_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS referees (
                referee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT NOT NULL,
                association TEXT
            );
        """)

    def create_event_types_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_types (
                event_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT
            );
        """)

    def create_matches_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                league_id INTEGER,
                matchday INTEGER,
                match_date TEXT,
                kickoff_time TEXT,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                stadium_id INTEGER,
                referee_id INTEGER,
                attendance INTEGER,
                home_goals INTEGER,
                away_goals INTEGER,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                FOREIGN KEY (season_id) REFERENCES seasons(season_id),
                FOREIGN KEY (league_id) REFERENCES leagues(league_id),
                FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
                FOREIGN KEY (stadium_id) REFERENCES stadiums(stadium_id),
                FOREIGN KEY (referee_id) REFERENCES referees(referee_id)
            );
        """)

    def create_lineups_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lineups (
                lineup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                is_starting INTEGER DEFAULT 0,
                shirt_number INTEGER,
                position TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(match_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id),
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            );
        """)

    def create_events_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                event_type_id INTEGER NOT NULL,
                minute INTEGER,
                second INTEGER DEFAULT 0,
                team_id INTEGER,
                player_id INTEGER,
                related_player_id INTEGER,
                value TEXT,
                notes TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(match_id),
                FOREIGN KEY (event_type_id) REFERENCES event_types(event_type_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id),
                FOREIGN KEY (player_id) REFERENCES players(player_id),
                FOREIGN KEY (related_player_id) REFERENCES players(player_id)
            );
        """)

    def create_formations_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS formations (
                formation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
        """)

    def create_match_formations_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_formations (
                match_formation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                formation_id INTEGER NOT NULL,
                FOREIGN KEY (match_id) REFERENCES matches(match_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id),
                FOREIGN KEY (formation_id) REFERENCES formations(formation_id)
            );
        """)

    def create_staff_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                first_name TEXT,
                last_name TEXT NOT NULL,
                role TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            );
        """)

    def create_weather_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                temperature REAL,
                condition TEXT,
                wind TEXT,
                notes TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            );
        """)

    def create_indexes(self):
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_matches_season_id ON matches(season_id);",
            "CREATE INDEX IF NOT EXISTS idx_matches_league_id ON matches(league_id);",
            "CREATE INDEX IF NOT EXISTS idx_matches_home_team_id ON matches(home_team_id);",
            "CREATE INDEX IF NOT EXISTS idx_matches_away_team_id ON matches(away_team_id);",
            "CREATE INDEX IF NOT EXISTS idx_events_match_id ON events(match_id);",
            "CREATE INDEX IF NOT EXISTS idx_events_player_id ON events(player_id);",
            "CREATE INDEX IF NOT EXISTS idx_events_team_id ON events(team_id);",
            "CREATE INDEX IF NOT EXISTS idx_lineups_match_id ON lineups(match_id);",
            "CREATE INDEX IF NOT EXISTS idx_lineups_player_id ON lineups(player_id);"
        ]

        for index in indexes:
            self.cursor.execute(index)

    def insert_default_event_types(self):
        event_types = [
            ("GOAL", "Tor", "Normales Tor"),
            ("OWN_GOAL", "Eigentor", "Eigentor"),
            ("YELLOW_CARD", "Gelbe Karte", "Verwarnung"),
            ("RED_CARD", "Rote Karte", "Platzverweis"),
            ("YELLOW_RED_CARD", "Gelb-Rote Karte", "Platzverweis nach zweiter Verwarnung"),
            ("SUBSTITUTION_IN", "Einwechslung", "Spieler wird eingewechselt"),
            ("SUBSTITUTION_OUT", "Auswechslung", "Spieler wird ausgewechselt"),
            ("PENALTY_GOAL", "Elfmetertor", "Verwandelter Elfmeter"),
            ("PENALTY_MISSED", "Elfmeter verschossen", "Nicht verwandelter Elfmeter"),
            ("INJURY", "Verletzung", "Verletzungsereignis")
        ]

        self.cursor.executemany("""
            INSERT OR IGNORE INTO event_types (code, name, description)
            VALUES (?, ?, ?);
        """, event_types)