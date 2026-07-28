from __future__ import annotations

import sqlite3

from src.validator.match_snapshot import MatchSnapshot


class SnapshotBuilder:
    """
    Erstellt einen MatchSnapshot aus der Datenbank.

    Diese Klasse bildet die einzige Schnittstelle zwischen
    SQLite und den Validatoren.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

    def build(
        self,
        match_id: str,
    ) -> MatchSnapshot:

        snapshot = MatchSnapshot(
            match_id=match_id,
        )

        return snapshot