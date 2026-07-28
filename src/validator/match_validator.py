from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from src.validator.validation_result import ValidationResult


@dataclass(frozen=True, slots=True)
class ValidationEvent:
    event_type: str
    minute: int | None
    team_name: str | None = None
    player_name: str | None = None
    related_player_name: str | None = None
    score_home: int | None = None
    score_away: int | None = None

    def comparison_key(self) -> tuple:
        return (
            self._normalize(self.event_type),
            self.minute,
            self._normalize(self.team_name),
            self._normalize(self.player_name),
            self._normalize(self.related_player_name),
            self.score_home,
            self.score_away,
        )

    @staticmethod
    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None

        return " ".join(value.casefold().split())


@dataclass(slots=True)
class MatchValidationSnapshot:
    home_team: str | None = None
    away_team: str | None = None

    home_score: int | None = None
    away_score: int | None = None

    halftime_home_score: int | None = None
    halftime_away_score: int | None = None

    match_date: str | None = None
    kickoff_time: str | None = None

    attendance: int | None = None
    referee: str | None = None
    stadium: str | None = None

    events: list[ValidationEvent] = field(default_factory=list)
    starting_lineup_home: list[str] = field(default_factory=list)
    starting_lineup_away: list[str] = field(default_factory=list)
    substitutes_home: list[str] = field(default_factory=list)
    substitutes_away: list[str] = field(default_factory=list)


class MatchValidator:
    def validate(
        self,
        source: MatchValidationSnapshot,
        database: MatchValidationSnapshot,
    ) -> ValidationResult:
        result = ValidationResult()

        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Heimmannschaft",
            expected=source.home_team,
            actual=database.home_team,
        )
        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Gastmannschaft",
            expected=source.away_team,
            actual=database.away_team,
        )
        self._compare_value(
            result,
            category="ERGEBNIS",
            label="Endstand Heim",
            expected=source.home_score,
            actual=database.home_score,
        )
        self._compare_value(
            result,
            category="ERGEBNIS",
            label="Endstand Gast",
            expected=source.away_score,
            actual=database.away_score,
        )
        self._compare_value(
            result,
            category="ERGEBNIS",
            label="Halbzeit Heim",
            expected=source.halftime_home_score,
            actual=database.halftime_home_score,
        )
        self._compare_value(
            result,
            category="ERGEBNIS",
            label="Halbzeit Gast",
            expected=source.halftime_away_score,
            actual=database.halftime_away_score,
        )
        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Datum",
            expected=source.match_date,
            actual=database.match_date,
        )
        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Anstoßzeit",
            expected=source.kickoff_time,
            actual=database.kickoff_time,
        )
        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Zuschauer",
            expected=source.attendance,
            actual=database.attendance,
        )
        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Schiedsrichter",
            expected=source.referee,
            actual=database.referee,
        )
        self._compare_value(
            result,
            category="SPIELKOPF",
            label="Spielstätte",
            expected=source.stadium,
            actual=database.stadium,
        )

        self._compare_events(
            result=result,
            expected_events=source.events,
            actual_events=database.events,
        )

        self._compare_player_lists(
            result=result,
            category="AUFSTELLUNG",
            label="Startelf Heim",
            expected=source.starting_lineup_home,
            actual=database.starting_lineup_home,
        )
        self._compare_player_lists(
            result=result,
            category="AUFSTELLUNG",
            label="Startelf Gast",
            expected=source.starting_lineup_away,
            actual=database.starting_lineup_away,
        )
        self._compare_player_lists(
            result=result,
            category="ERSATZBANK",
            label="Ersatzbank Heim",
            expected=source.substitutes_home,
            actual=database.substitutes_home,
        )
        self._compare_player_lists(
            result=result,
            category="ERSATZBANK",
            label="Ersatzbank Gast",
            expected=source.substitutes_away,
            actual=database.substitutes_away,
        )

        return result

    def _compare_value(
        self,
        result: ValidationResult,
        category: str,
        label: str,
        expected: object,
        actual: object,
    ) -> None:
        normalized_expected = self._normalize_value(expected)
        normalized_actual = self._normalize_value(actual)

        if normalized_expected == normalized_actual:
            result.success()
            return

        result.error(
            category=category,
            message=(
                f"{label}: erwartet {expected!r}, "
                f"gespeichert {actual!r}"
            ),
        )

    def _compare_events(
        self,
        result: ValidationResult,
        expected_events: Iterable[ValidationEvent],
        actual_events: Iterable[ValidationEvent],
    ) -> None:
        expected_counter = Counter(
            event.comparison_key()
            for event in expected_events
        )
        actual_counter = Counter(
            event.comparison_key()
            for event in actual_events
        )

        missing_events = expected_counter - actual_counter
        additional_events = actual_counter - expected_counter

        if not missing_events and not additional_events:
            result.success()
            return

        for event_key, count in missing_events.items():
            result.error(
                category="EVENTS",
                message=(
                    f"Event fehlt ({count}×): "
                    f"{self._format_event_key(event_key)}"
                ),
            )

        for event_key, count in additional_events.items():
            result.error(
                category="EVENTS",
                message=(
                    f"Zusätzliches Event ({count}×): "
                    f"{self._format_event_key(event_key)}"
                ),
            )

    def _compare_player_lists(
        self,
        result: ValidationResult,
        category: str,
        label: str,
        expected: Iterable[str],
        actual: Iterable[str],
    ) -> None:
        expected_counter = Counter(
            self._normalize_text(player)
            for player in expected
            if player
        )
        actual_counter = Counter(
            self._normalize_text(player)
            for player in actual
            if player
        )

        missing_players = expected_counter - actual_counter
        additional_players = actual_counter - expected_counter

        if not missing_players and not additional_players:
            result.success()
            return

        for player, count in missing_players.items():
            result.error(
                category=category,
                message=f"{label}: Spieler fehlt ({count}×): {player}",
            )

        for player, count in additional_players.items():
            result.error(
                category=category,
                message=(
                    f"{label}: zusätzlicher Spieler "
                    f"({count}×): {player}"
                ),
            )

    @staticmethod
    def _normalize_value(value: object) -> object:
        if isinstance(value, str):
            return MatchValidator._normalize_text(value)

        return value

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.casefold().split())

    @staticmethod
    def _format_event_key(event_key: tuple) -> str:
        (
            event_type,
            minute,
            team_name,
            player_name,
            related_player_name,
            score_home,
            score_away,
        ) = event_key

        parts = [
            f"Typ={event_type}",
            f"Minute={minute}",
        ]

        if team_name:
            parts.append(f"Team={team_name}")

        if player_name:
            parts.append(f"Spieler={player_name}")

        if related_player_name:
            parts.append(
                f"Zugehöriger Spieler={related_player_name}"
            )

        if score_home is not None and score_away is not None:
            parts.append(f"Spielstand={score_home}:{score_away}")

        return ", ".join(parts)