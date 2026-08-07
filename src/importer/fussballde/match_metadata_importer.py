from __future__ import annotations

import sqlite3

from src.database.repositories.referee_repository import (
    RefereeRepository,
)
from src.database.repositories.stadium_repository import (
    StadiumRepository,
)
from src.importer.fussballde.match_notes_builder import (
    MatchNotesBuilder,
)


class MatchMetadataImporter:
    """
    Importiert Zusatzdaten eines Spiels, die nicht direkt
    zu Ereignissen oder Aufstellungen gehören.

    Aktuell:
    - Spielstätte
    - Schiedsrichter
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

        self.referee_repository = (
            RefereeRepository(
                connection
            )
        )

        self.stadium_repository = (
            StadiumRepository(
                connection
            )
        )

    def import_stadium(
        self,
        stadium_name: str,
    ) -> int | None:
        normalized_name = (
            MatchNotesBuilder
            .clean_import_text(
                stadium_name
            )
        )

        if not normalized_name:
            return None

        return (
            self.stadium_repository
            .get_or_create(
                name=normalized_name,
                commit=False,
            )
        )

    def import_referee(
        self,
        referee_name: str,
    ) -> int | None:
        normalized_name = (
            MatchNotesBuilder
            .clean_import_text(
                referee_name
            )
        )

        normalized_name = (
            MatchNotesBuilder
            .remove_referee_suffixes(
                normalized_name
            )
        )

        if not normalized_name:
            return None

        return (
            self.referee_repository
            .get_or_create_by_full_name(
                full_name=normalized_name,
                commit=False,
            )
        )

    def import_all(
        self,
        stadium_name: str,
        referee_name: str,
    ) -> dict:
        stadium_id = self.import_stadium(
            stadium_name
        )

        referee_id = self.import_referee(
            referee_name
        )

        return {
            "stadium_id": stadium_id,
            "referee_id": referee_id,
        }