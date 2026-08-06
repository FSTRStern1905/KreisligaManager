from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class LivetickerEvent:
    minute: int | None = None
    additional_time: int = 0
    event_type: str = "unknown"
    team: str = ""
    player: str = ""
    player_id: str = ""
    player_out: str = ""
    player_out_id: str = ""
    score_home: int | None = None
    score_away: int | None = None
    title: str = ""
    description: str = ""
    source_event_id: str = ""
    raw_data: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def display_minute(self) -> str:
        if self.minute is None:
            return ""

        if self.additional_time > 0:
            return (
                f"{self.minute}"
                f"+{self.additional_time}"
            )

        return str(
            self.minute
        )

    @property
    def has_player_assignment(self) -> bool:
        return bool(
            self.player.strip()
            or self.player_id.strip()
        )

    @property
    def has_score(self) -> bool:
        return (
            self.score_home is not None
            and self.score_away is not None
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(
            self
        )


@dataclass(slots=True)
class LivetickerData:
    source_url: str = ""
    match_id: str = ""
    page_title: str = ""
    competition: str = ""
    home_team: str = ""
    away_team: str = ""
    home_score: int | None = None
    away_score: int | None = None
    ticker_available: bool = False
    source_type: str = ""
    events: list[LivetickerEvent] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def event_count(self) -> int:
        return len(
            self.events
        )

    @property
    def assigned_event_count(self) -> int:
        return sum(
            event.has_player_assignment
            for event in self.events
        )

    @property
    def unassigned_event_count(self) -> int:
        return (
            self.event_count
            - self.assigned_event_count
        )

    @property
    def player_assignment_rate(self) -> float:
        if not self.events:
            return 100.0

        return (
            self.assigned_event_count
            / self.event_count
            * 100
        )

    def get_events_by_type(
        self,
        event_type: str,
    ) -> list[LivetickerEvent]:
        normalized_type = (
            event_type
            .strip()
            .casefold()
        )

        return [
            event
            for event in self.events
            if (
                event.event_type
                .strip()
                .casefold()
                == normalized_type
            )
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "match_id": self.match_id,
            "page_title": self.page_title,
            "competition": self.competition,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "ticker_available": (
                self.ticker_available
            ),
            "source_type": self.source_type,
            "event_count": self.event_count,
            "assigned_event_count": (
                self.assigned_event_count
            ),
            "unassigned_event_count": (
                self.unassigned_event_count
            ),
            "player_assignment_rate": round(
                self.player_assignment_rate,
                1,
            ),
            "events": [
                event.to_dict()
                for event in self.events
            ],
            "warnings": list(
                self.warnings
            ),
        }