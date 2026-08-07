from __future__ import annotations

import sqlite3
from typing import Any

from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.importer.fussballde.parsers.match_detail_data import (
    MatchDetailData,
)
from src.importer.fussballde.parsers.match_detail_parser import (
    MatchDetailParser,
)
from src.importer.fussballde.match_notes_builder import (
    MatchNotesBuilder,
)
from src.importer.fussballde.match_metadata_importer import (
    MatchMetadataImporter,
)
from src.importer.fussballde.match_page_loader import (
    MatchPageLoader,
)
from src.importer.fussballde.match_event_importer import (
    MatchEventImporter,
)

from src.importer.fussballde.lineup_importer import (
    LineupImporter,
)
from src.importer.fussballde.liveticker_data import (
    LivetickerData,
)
from src.importer.fussballde.liveticker_loader import (
    LivetickerLoader,
)

from src.services.statistics.statistics_updater import (
    StatisticsUpdater,
)

class MatchDetailImporter:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

        self.match_repository = MatchRepository(
            connection
        )
        self.metadata_importer = (
            MatchMetadataImporter(
                connection
            )
        )

        self.event_importer = (
            MatchEventImporter(
                connection
            )
        )

        self.liveticker_loader = (
            LivetickerLoader()
        )

        self.page_loader = (
            MatchPageLoader()
        )

        self.lineup_importer = LineupImporter(
            connection
        )
        self.statistics_updater = (
            StatisticsUpdater(
                connection
            )
        )

    def import_from_page(
        self,
        page: Any,
        source_url: str,
    ) -> dict:
        if page is None:
            raise ValueError(
                "Es wurde keine Browserseite übergeben."
            )

        normalized_url = source_url.strip()

        if not normalized_url:
            raise ValueError(
                "Die Spiel-URL darf nicht leer sein."
            )

        html = self.page_loader.load(
            page=page,
            source_url=normalized_url,
        )

        parser = MatchDetailParser(
            page
        )

        detail_data = parser.parse(
            html=html,
            source_url=normalized_url,
        )

        lineup_result = (
            self.lineup_importer
            .import_from_page(
                page=page,
                match_external_id=(
                    detail_data.match_id
                ),
            )
        )

        liveticker_data = (
            self.liveticker_loader.load(
                page=page,
                source_url=normalized_url,
                match_external_id=(
                    detail_data.match_id
                ),
            )
        )

        result = self.import_data(
            detail_data=detail_data,
            source_url=normalized_url,
            liveticker_data=liveticker_data,
        )

        result["lineups_imported"] = (
            lineup_result[
                "lineups_imported"
            ]
        )

        result[
            "lineup_players_imported"
        ] = lineup_result[
            "players_imported"
        ]

        result["liveticker_available"] = (
            liveticker_data is not None
        )

        result["event_source"] = (
            "liveticker_json"
            if liveticker_data is not None
            else "match_html"
        )

        return result



    def import_from_html(
        self,
        html: str,
        source_url: str,
        page: Any = None,
    ) -> dict:
        normalized_html = html.strip()
        normalized_url = source_url.strip()

        if not normalized_html:
            raise ValueError(
                "Der HTML-Inhalt darf nicht leer sein."
            )

        if not normalized_url:
            raise ValueError(
                "Die Spiel-URL darf nicht leer sein."
            )

        parser = MatchDetailParser(page)

        detail_data = parser.parse(
            html=normalized_html,
            source_url=normalized_url,
        )

        return self.import_data(
            detail_data=detail_data,
            source_url=normalized_url,
        )

    def import_data(
        self,
        detail_data: MatchDetailData,
        source_url: str = "",
        liveticker_data: LivetickerData | None = None,
    ) -> dict:
        external_id = detail_data.match_id.strip()

        if not external_id:
            raise ValueError(
                "Die externe Spiel-ID konnte nicht "
                "ermittelt werden."
            )

        database_match = (
            self.match_repository.get_by_external_id(
                external_id
            )
        )

        if database_match is None:
            raise ValueError(
                "Das Spiel wurde nicht in der Datenbank "
                f"gefunden: {external_id}"
            )

        if database_match.match_id is None:
            raise ValueError(
                "Das gefundene Spiel besitzt keine "
                "interne Spiel-ID."
            )

        if database_match.home_team_id is None:
            raise ValueError(
                "Das Spiel besitzt keine "
                "Heimmannschaft."
            )

        if database_match.away_team_id is None:
            raise ValueError(
                "Das Spiel besitzt keine "
                "Auswärtsmannschaft."
            )

        match_id = int(
            database_match.match_id
        )

        self._validate_teams(
            detail_data=detail_data,
            database_match=database_match,
        )

        try:
            metadata_result = (
                self.metadata_importer
                .import_all(
                    stadium_name=detail_data.stadium,
                    referee_name=detail_data.referee,
                )
            )

            stadium_id = metadata_result[
                "stadium_id"
            ]

            referee_id = metadata_result[
                "referee_id"
            ]

            database_match.stadium_id = stadium_id
            database_match.referee_id = referee_id

            self._update_match(
                database_match=database_match,
                detail_data=detail_data,
                source_url=source_url,
            )

            (
                imported_event_count,
                player_ids,
            ) = self.event_importer.import_events(
                match_id=match_id,
                detail_data=detail_data,
                home_team_id=int(
                    database_match.home_team_id
                ),
                away_team_id=int(
                    database_match.away_team_id
                ),
                liveticker_data=liveticker_data,
            )

            statistics_result = (
                self.statistics_updater
                .update_match(
                    match_id
                )
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        return {
            "match_id": match_id,
            "external_id": external_id,
            "home_team": detail_data.home_team,
            "away_team": detail_data.away_team,
            "home_goals": detail_data.home_goals,
            "away_goals": detail_data.away_goals,
            "stadium_id": stadium_id,
            "referee_id": referee_id,
            "players_imported": len(player_ids),
            "events_imported":
                imported_event_count,
            "event_source": (
                "liveticker_json"
                if liveticker_data is not None
                else "match_html"
            ),
            "player_match_stats_created": (
                statistics_result[
                    "player_match_stats_created"
                ]
            ),
        }    

    def _update_match(
        self,
        database_match,
        detail_data: MatchDetailData,
        source_url: str,
    ) -> None:
        if detail_data.home_goals is not None:
            database_match.home_goals = (
                detail_data.home_goals
            )

        if detail_data.away_goals is not None:
            database_match.away_goals = (
                detail_data.away_goals
            )

        if detail_data.attendance is not None:
            database_match.attendance = (
                detail_data.attendance
            )

        if (
            detail_data.home_goals is not None
            and detail_data.away_goals is not None
        ):
            database_match.status = "finished"

        database_match.notes = (
            MatchNotesBuilder.build(
                existing_notes=database_match.notes,
                detail_data=detail_data,
                source_url=source_url,
            )
        )
        database_match.detail_imported = 1
        
        self.match_repository.update(
            database_match
        )



    def _validate_teams(
        self,
        detail_data: MatchDetailData,
        database_match,
    ) -> None:
        parsed_home = self._normalize_name(
            detail_data.home_team
        )

        parsed_away = self._normalize_name(
            detail_data.away_team
        )

        database_home = self._normalize_name(
            database_match.home_team_name
        )

        database_away = self._normalize_name(
            database_match.away_team_name
        )

        if (
            parsed_home
            and database_home
            and parsed_home != database_home
        ):
            raise ValueError(
                "Die Heimmannschaft der Detailseite "
                "passt nicht zum gespeicherten Spiel:\n"
                f"{detail_data.home_team} != "
                f"{database_match.home_team_name}"
            )

        if (
            parsed_away
            and database_away
            and parsed_away != database_away
        ):
            raise ValueError(
                "Die Auswärtsmannschaft der Detailseite "
                "passt nicht zum gespeicherten Spiel:\n"
                f"{detail_data.away_team} != "
                f"{database_match.away_team_name}"
            )


    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        return " ".join(
            value.split()
        ).casefold()


    @classmethod
    def _clean_import_text(
        cls,
        value: str,
        allow_private_unicode: bool = False,
    ) -> str:
        normalized = " ".join(
            (value or "").split()
        )

        if not normalized:
            return ""

        if (
            not allow_private_unicode
            and cls._contains_private_unicode(
                normalized
            )
        ):
            return ""

        return normalized.strip(
            " -|,;"
        )

    @staticmethod
    def _contains_private_unicode(
        value: str,
    ) -> bool:
        return any(
            0xE000 <= ord(character) <= 0xF8FF
            for character in value
        )

    @staticmethod
    def _remove_referee_suffixes(
        referee_name: str,
    ) -> str:
        normalized_name = referee_name.strip()

        suffixes = (
            " Assistenten:",
            " Assistent:",
            " Schiedsrichterassistenten:",
            " Schiedsrichter-Assistenten:",
        )

        for suffix in suffixes:
            position = normalized_name.casefold().find(
                suffix.casefold()
            )

            if position >= 0:
                normalized_name = (
                    normalized_name[:position]
                ).strip()

        return normalized_name