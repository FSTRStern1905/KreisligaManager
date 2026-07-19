import sqlite3


class EventTypesSeed:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection
        self.cursor = connection.cursor()

    def seed(self) -> None:
        event_types = [
            ("GOAL", "Tor", "Normales Tor"),
            ("OWN_GOAL", "Eigentor", "Eigentor"),
            ("YELLOW_CARD", "Gelbe Karte", "Verwarnung"),
            ("RED_CARD", "Rote Karte", "Platzverweis"),
            (
                "YELLOW_RED_CARD",
                "Gelb-Rote Karte",
                "Platzverweis nach zweiter Verwarnung",
            ),
            (
                "SUBSTITUTION_IN",
                "Einwechslung",
                "Spieler wird eingewechselt",
            ),
            (
                "SUBSTITUTION_OUT",
                "Auswechslung",
                "Spieler wird ausgewechselt",
            ),
            (
                "PENALTY_GOAL",
                "Elfmetertor",
                "Verwandelter Elfmeter",
            ),
            (
                "PENALTY_MISSED",
                "Elfmeter verschossen",
                "Nicht verwandelter Elfmeter",
            ),
            (
                "INJURY",
                "Verletzung",
                "Verletzungsereignis",
            ),
        ]

        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO event_types (
                code,
                name,
                description
            )
            VALUES (?, ?, ?);
            """,
            event_types,
        )