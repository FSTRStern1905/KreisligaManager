from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SnapshotPlayer:
    player_id: str = ""
    name: str = ""
    team: str = ""
    number: int | None = None
    position: str = ""
    is_starting: bool = False
    is_captain: bool = False


@dataclass(slots=True)
class SnapshotEvent:
    minute: int | None = None
    additional_time: int = 0

    event_type: str = ""

    team: str = ""

    player: str = ""
    player_id: str = ""

    player_out: str = ""
    player_out_id: str = ""

    home_goals: int | None = None
    away_goals: int | None = None

    value: str = ""
    description: str = ""


@dataclass(slots=True)
class MatchSnapshot:
    """
    Vollständiger Zustand eines Spiels aus der Datenbank.

    Dieses Objekt ist die einzige Datenquelle für alle Validatoren.
    """

    match_id: str = ""

    home_team: str = ""
    away_team: str = ""

    home_goals: int | None = None
    away_goals: int | None = None

    halftime_home: int | None = None
    halftime_away: int | None = None

    stadium: str = ""
    referee: str = ""
    attendance: int | None = None

    home_players: list[SnapshotPlayer] = field(
        default_factory=list
    )

    away_players: list[SnapshotPlayer] = field(
        default_factory=list
    )

    events: list[SnapshotEvent] = field(
        default_factory=list
    )