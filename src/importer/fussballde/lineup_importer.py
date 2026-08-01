from __future__ import annotations

import sqlite3
from typing import Any

from src.database.repositories.lineup_repository import (
    LineupRepository,
)
from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.importer.fussballde.parsers.lineup_data import (
    LineupPlayer,
    MatchLineup,
    TeamLineup,
)
from src.importer.fussballde.parsers.lineup_parser import (
    LineupParser,
)


class LineupImporter:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

        self.match_repository = MatchRepository(
            connection
        )

        self.player_repository = PlayerRepository(
            connection
        )

        self.lineup_repository = LineupRepository(
            connection
        )

    def import_from_html(
        self,
        html: str,
        match_external_id: str,
        request_context: Any | None = None,
    ) -> dict:
        normalized_html = html.strip()
        normalized_external_id = (
            match_external_id.strip()
        )

        if not normalized_html:
            raise ValueError(
                "Der HTML-Inhalt der Aufstellung "
                "darf nicht leer sein."
            )

        if not normalized_external_id:
            raise ValueError(
                "Die externe Spiel-ID darf "
                "nicht leer sein."
            )

        parser = LineupParser(
            request_context=request_context,
        )

        lineup = parser.parse(
            normalized_html
        )

        return self.import_data(
            lineup=lineup,
            match_external_id=normalized_external_id,
        )

    def import_data(
        self,
        lineup: MatchLineup,
        match_external_id: str,
    ) -> dict:
        normalized_external_id = (
            match_external_id.strip()
        )

        if not normalized_external_id:
            raise ValueError(
                "Die externe Spiel-ID darf "
                "nicht leer sein."
            )

        database_match = (
            self.match_repository.get_by_external_id(
                normalized_external_id
            )
        )

        if database_match is None:
            raise ValueError(
                "Das Spiel wurde nicht in der "
                "Datenbank gefunden: "
                f"{normalized_external_id}"
            )

        if database_match.match_id is None:
            raise ValueError(
                "Das Spiel besitzt keine interne "
                "Spiel-ID."
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

        home_team_id = int(
            database_match.home_team_id
        )

        away_team_id = int(
            database_match.away_team_id
        )

        self._validate_team_names(
            lineup=lineup,
            database_match=database_match,
        )

        try:
            home_rows, home_player_ids = (
                self._build_team_rows(
                    match_id=match_id,
                    team_id=home_team_id,
                    team_lineup=lineup.home,
                )
            )

            away_rows, away_player_ids = (
                self._build_team_rows(
                    match_id=match_id,
                    team_id=away_team_id,
                    team_lineup=lineup.away,
                )
            )

            lineup_rows = [
                *home_rows,
                *away_rows,
            ]

            inserted_count = (
                self.lineup_repository
                .replace_match_lineups(
                    match_id=match_id,
                    lineups=lineup_rows,
                )
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        return {
            "match_id": match_id,
            "external_id": normalized_external_id,
            "home_team": lineup.home.team_name,
            "away_team": lineup.away.team_name,
            "home_players_imported": len(
                home_player_ids
            ),
            "away_players_imported": len(
                away_player_ids
            ),
            "players_imported": len(
                home_player_ids
                | away_player_ids
            ),
            "home_starters": len(
                lineup.home.starting
            ),
            "away_starters": len(
                lineup.away.starting
            ),
            "home_substitutes": len(
                lineup.home.substitutes
            ),
            "away_substitutes": len(
                lineup.away.substitutes
            ),
            "lineups_imported": inserted_count,
            "home_coach": lineup.home.coach,
            "away_coach": lineup.away.coach,
        }

    def _build_team_rows(
        self,
        match_id: int,
        team_id: int,
        team_lineup: TeamLineup,
    ) -> tuple[list[dict], set[int]]:
        rows: list[dict] = []
        player_ids: set[int] = set()

        for player in team_lineup.players:
            player_id = self._resolve_player(
                player=player,
                team_id=team_id,
            )

            position = self._resolve_position(
                player
            )

            rows.append(
                {
                    "match_id": match_id,
                    "team_id": team_id,
                    "player_id": player_id,
                    "is_starting":
                        player.is_starting,
                    "shirt_number":
                        player.shirt_number,
                    "position": position,
                }
            )

            player_ids.add(
                player_id
            )

        return rows, player_ids

    def _resolve_player(
        self,
        player: LineupPlayer,
        team_id: int,
    ) -> int:
        first_name, last_name = (
            self._normalize_player_name(
                first_name=player.first_name,
                last_name=player.last_name,
                external_id=player.external_id,
            )
        )

        return (
            self.player_repository.get_or_create(
                first_name=first_name,
                last_name=last_name,
                team_id=team_id,
                external_id=player.external_id,
                commit=False,
            )
        )

    @staticmethod
    def _normalize_player_name(
        first_name: str,
        last_name: str,
        external_id: str,
    ) -> tuple[str, str]:
        normalized_first_name = " ".join(
            first_name.split()
        )

        normalized_last_name = " ".join(
            last_name.split()
        )

        normalized_external_id = (
            external_id.strip()
        )

        if normalized_last_name:
            return (
                normalized_first_name,
                normalized_last_name,
            )

        if normalized_first_name:
            return (
                "",
                normalized_first_name,
            )

        if normalized_external_id:
            return (
                "",
                f"Unbekannt {normalized_external_id}",
            )

        raise ValueError(
            "Ein Aufstellungsspieler besitzt weder "
            "einen Namen noch eine externe ID."
        )

    @staticmethod
    def _resolve_position(
        player: LineupPlayer,
    ) -> str:
        if player.is_goalkeeper:
            return "Torwart"

        return ""

    def _validate_team_names(
        self,
        lineup: MatchLineup,
        database_match: Any,
    ) -> None:
        parsed_home = self._normalize_team_name(
            lineup.home.team_name
        )

        parsed_away = self._normalize_team_name(
            lineup.away.team_name
        )

        database_home = self._normalize_team_name(
            database_match.home_team_name
        )

        database_away = self._normalize_team_name(
            database_match.away_team_name
        )

        if (
            parsed_home
            and database_home
            and parsed_home != database_home
        ):
            raise ValueError(
                "Die Heimmannschaft der Aufstellung "
                "passt nicht zum gespeicherten Spiel:\n"
                f"{lineup.home.team_name} != "
                f"{database_match.home_team_name}"
            )

        if (
            parsed_away
            and database_away
            and parsed_away != database_away
        ):
            raise ValueError(
                "Die Auswärtsmannschaft der "
                "Aufstellung passt nicht zum "
                "gespeicherten Spiel:\n"
                f"{lineup.away.team_name} != "
                f"{database_match.away_team_name}"
            )

    @staticmethod
    def _normalize_team_name(
        value: str,
    ) -> str:
        return " ".join(
            (value or "").split()
        ).casefold()