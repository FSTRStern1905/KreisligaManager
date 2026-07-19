import sqlite3


class WeatherTable:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS weather (
                weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                temperature REAL,
                feels_like REAL,
                humidity INTEGER,
                wind_speed REAL,
                wind_direction TEXT,
                precipitation REAL,
                condition TEXT,
                notes TEXT,
                external_id TEXT,

                FOREIGN KEY (match_id)
                    REFERENCES matches(match_id)
                    ON DELETE CASCADE
            );
            """
        )