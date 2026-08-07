from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ImportResult:
    """
    Zentrales Ergebnisobjekt für Importvorgänge.

    Die bisherigen Felder bleiben erhalten, damit bestehende
    Import-Services rückwärtskompatibel weiterarbeiten können.

    Zusätzlich können Importer Warnungen, Fehler, Laufzeit und
    Detailstatistiken sammeln.
    """

    competitions_created: int = 0
    clubs_created: int = 0
    teams_created: int = 0
    matches_created: int = 0
    matches_updated: int = 0

    players_created: int = 0
    players_updated: int = 0

    lineups_imported: int = 0
    substitutions_imported: int = 0
    events_imported: int = 0

    goals_imported: int = 0
    own_goals_imported: int = 0
    yellow_cards_imported: int = 0
    yellow_red_cards_imported: int = 0
    red_cards_imported: int = 0
    penalties_missed_imported: int = 0

    referees_created: int = 0
    stadiums_created: int = 0

    matches_found: int = 0
    match_details_imported: int = 0
    match_details_failed: int = 0

    duration_seconds: float = 0.0

    warnings: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    @property
    def success(self) -> bool:
        return not self.errors

    @property
    def has_warnings(self) -> bool:
        return bool(
            self.warnings
        )

    @property
    def has_errors(self) -> bool:
        return bool(
            self.errors
        )

    @property
    def players_imported(self) -> int:
        return (
            self.players_created
            + self.players_updated
        )

    @property
    def matches_imported(self) -> int:
        return (
            self.matches_created
            + self.matches_updated
        )

    @property
    def cards_imported(self) -> int:
        return (
            self.yellow_cards_imported
            + self.yellow_red_cards_imported
            + self.red_cards_imported
        )

    @property
    def total_changes(self) -> int:
        return (
            self.competitions_created
            + self.clubs_created
            + self.teams_created
            + self.matches_created
            + self.matches_updated
            + self.players_created
            + self.players_updated
            + self.lineups_imported
            + self.substitutions_imported
            + self.events_imported
            + self.referees_created
            + self.stadiums_created
        )

    def add_warning(
        self,
        message: str,
    ) -> None:
        normalized_message = (
            message.strip()
        )

        if (
            normalized_message
            and normalized_message
            not in self.warnings
        ):
            self.warnings.append(
                normalized_message
            )

    def add_error(
        self,
        message: str,
    ) -> None:
        normalized_message = (
            message.strip()
        )

        if (
            normalized_message
            and normalized_message
            not in self.errors
        ):
            self.errors.append(
                normalized_message
            )

    def merge(
        self,
        other: ImportResult,
    ) -> None:
        """
        Addiert ein weiteres ImportResult auf dieses Ergebnis.

        Dadurch können später einzelne Import-Schritte unabhängig
        voneinander arbeiten und ihr Ergebnis an den zentralen
        Saisonimport zurückgeben.
        """
        numeric_fields = (
            "competitions_created",
            "clubs_created",
            "teams_created",
            "matches_created",
            "matches_updated",
            "players_created",
            "players_updated",
            "lineups_imported",
            "substitutions_imported",
            "events_imported",
            "goals_imported",
            "own_goals_imported",
            "yellow_cards_imported",
            "yellow_red_cards_imported",
            "red_cards_imported",
            "penalties_missed_imported",
            "referees_created",
            "stadiums_created",
            "matches_found",
            "match_details_imported",
            "match_details_failed",
        )

        for field_name in numeric_fields:
            setattr(
                self,
                field_name,
                getattr(
                    self,
                    field_name,
                )
                + getattr(
                    other,
                    field_name,
                ),
            )

        self.duration_seconds += (
            other.duration_seconds
        )

        for warning in other.warnings:
            self.add_warning(
                warning
            )

        for error in other.errors:
            self.add_error(
                error
            )

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "has_warnings": self.has_warnings,
            "has_errors": self.has_errors,
            "competitions_created": (
                self.competitions_created
            ),
            "clubs_created": self.clubs_created,
            "teams_created": self.teams_created,
            "matches_created": self.matches_created,
            "matches_updated": self.matches_updated,
            "matches_imported": self.matches_imported,
            "players_created": self.players_created,
            "players_updated": self.players_updated,
            "players_imported": self.players_imported,
            "lineups_imported": self.lineups_imported,
            "substitutions_imported": (
                self.substitutions_imported
            ),
            "events_imported": self.events_imported,
            "goals_imported": self.goals_imported,
            "own_goals_imported": (
                self.own_goals_imported
            ),
            "yellow_cards_imported": (
                self.yellow_cards_imported
            ),
            "yellow_red_cards_imported": (
                self.yellow_red_cards_imported
            ),
            "red_cards_imported": (
                self.red_cards_imported
            ),
            "cards_imported": self.cards_imported,
            "penalties_missed_imported": (
                self.penalties_missed_imported
            ),
            "referees_created": self.referees_created,
            "stadiums_created": self.stadiums_created,
            "matches_found": self.matches_found,
            "match_details_imported": (
                self.match_details_imported
            ),
            "match_details_failed": (
                self.match_details_failed
            ),
            "duration_seconds": round(
                self.duration_seconds,
                3,
            ),
            "warnings": list(
                self.warnings
            ),
            "errors": list(
                self.errors
            ),
            "total_changes": self.total_changes,
        }