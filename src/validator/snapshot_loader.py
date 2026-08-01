from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.database.repositories.event_repository import (
    EventRepository,
)
from src.database.repositories.lineup_repository import (
    LineupRepository,
)
from src.database.repositories.match_repository import (
    MatchRepository,
)
from src.database.repositories.player_repository import (
    PlayerRepository,
)
from src.database.repositories.referee_repository import (
    RefereeRepository,
)
from src.database.repositories.stadium_repository import (
    StadiumRepository,
)


@dataclass(slots=True)
class LoadedMatchData:
    match: Any
    home_players: list[dict]
    away_players: list[dict]
    lineups: list[dict]
    events: list[dict]
    referee: dict | None
    stadium: dict | None


class SnapshotLoader:
    """
    Lädt alle Daten eines Spiels über die Repositorys.

    Der Loader erstellt noch keinen MatchSnapshot.
    Er liefert ausschließlich die Rohdaten aus der Datenbank.
    """

    def __init__(
        self,
        match_repository: MatchRepository,
        player_repository: PlayerRepository,
        lineup_repository: LineupRepository,
        event_repository: EventRepository,
        referee_repository: RefereeRepository,
        stadium_repository: StadiumRepository,
    ) -> None:
        self.match_repository = match_repository
        self.player_repository = player_repository
        self.lineup_repository = lineup_repository
        self.event_repository = event_repository
        self.referee_repository = referee_repository
        self.stadium_repository = stadium_repository

    def load_by_external_id(
        self,
        external_id: str,
    ) -> LoadedMatchData:
        normalized_external_id = external_id.strip()

        if not normalized_external_id:
            raise ValueError(
                "Die externe Spiel-ID darf nicht leer sein."
            )

        match = self.match_repository.get_by_external_id(
            normalized_external_id
        )

        if match is None:
            raise ValueError(
                "Das Spiel wurde nicht gefunden: "
                f"{normalized_external_id}"
            )

        if match.match_id is None:
            raise ValueError(
                "Das Spiel besitzt keine interne Spiel-ID."
            )

        if match.home_team_id is None:
            raise ValueError(
                "Das Spiel besitzt keine Heim-Mannschaft."
            )

        if match.away_team_id is None:
            raise ValueError(
                "Das Spiel besitzt keine Auswärts-Mannschaft."
            )

        match_id = int(match.match_id)
        home_team_id = int(match.home_team_id)
        away_team_id = int(match.away_team_id)

        home_players = self.player_repository.get_by_team(
            team_id=home_team_id,
        )

        away_players = self.player_repository.get_by_team(
            team_id=away_team_id,
        )

        lineups = self.lineup_repository.get_by_match(
            match_id=match_id,
        )

        events = self.event_repository.get_by_match(
            match_id=match_id,
        )

        referee = None

        if match.referee_id is not None:
            referee = self.referee_repository.get(
                int(match.referee_id)
            )

        stadium = None

        if match.stadium_id is not None:
            stadium = self.stadium_repository.get(
                int(match.stadium_id)
            )

        return LoadedMatchData(
            match=match,
            home_players=home_players,
            away_players=away_players,
            lineups=lineups,
            events=events,
            referee=referee,
            stadium=stadium,
        )