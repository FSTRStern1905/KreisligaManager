import sqlite3


class PlayerMatchStatsTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_match_stats (
                player_match_stat_id INTEGER PRIMARY KEY AUTOINCREMENT,

                match_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,

                is_starting INTEGER NOT NULL DEFAULT 0,

                was_substituted_in INTEGER NOT NULL DEFAULT 0,
                was_substituted_out INTEGER NOT NULL DEFAULT 0,

                minute_in INTEGER,
                minute_out INTEGER,
                minutes_played INTEGER NOT NULL DEFAULT 0,

                goals INTEGER NOT NULL DEFAULT 0,
                own_goals INTEGER NOT NULL DEFAULT 0,
                assists INTEGER NOT NULL DEFAULT 0,

                yellow_cards INTEGER NOT NULL DEFAULT 0,
                yellow_red_cards INTEGER NOT NULL DEFAULT 0,
                red_cards INTEGER NOT NULL DEFAULT 0,

                clean_sheet INTEGER NOT NULL DEFAULT 0,

                shirt_number INTEGER,
                position TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (match_id)
                    REFERENCES matches(match_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (team_id)
                    REFERENCES teams(team_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE CASCADE,

                UNIQUE (
                    match_id,
                    player_id
                )
            );
            """
        )