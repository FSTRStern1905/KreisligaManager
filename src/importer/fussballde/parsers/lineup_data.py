from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class LineupPlayer:
    external_id: str
    first_name: str
    last_name: str
    shirt_number: int | None = None

    is_starting: bool = False
    is_substitute: bool = False

    is_goalkeeper: bool = False
    is_captain: bool = False

    team_name: str = ""

    @property
    def full_name(self) -> str:
        return " ".join(
            part
            for part in (
                self.first_name,
                self.last_name,
            )
            if part
        )


@dataclass(slots=True)
class TeamLineup:
    team_name: str

    starting: list[LineupPlayer] = field(
        default_factory=list
    )

    substitutes: list[LineupPlayer] = field(
        default_factory=list
    )

    coach: str = ""

    @property
    def players(self) -> list[LineupPlayer]:
        return [
            *self.starting,
            *self.substitutes,
        ]


@dataclass(slots=True)
class MatchLineup:
    home: TeamLineup
    away: TeamLineup

    @property
    def players(self) -> list[LineupPlayer]:
        return [
            *self.home.players,
            *self.away.players,
        ]