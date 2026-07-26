from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.standing_repository import (
    StandingRepository,
)
from src.importer.fussballde.parsers.standings_data import (
    StandingRow,
    StandingsData,
)


@dataclass(slots=True)
class StandingsImportResult:
    rows_imported: int = 0
    rows_updated: int = 0
    unmatched_teams: tuple[str, ...] = ()

    @property
    def total_changes(self) -> int:
        return self.rows_imported + self.rows_updated


class StandingsImportService:

    WHITESPACE_PATTERN = re.compile(r"\s+")
    PUNCTUATION_PATTERN = re.compile(r"[^a-z0-9äöüß]+")

    def __init__(
        self,
        competition_repository: CompetitionRepository,
        standing_repository: StandingRepository,
    ) -> None:
        self.competition_repository = competition_repository
        self.standing_repository = standing_repository
        self.connection = standing_repository.connection

    def import_standings(
        self,
        competition_id: int,
        standings_data: StandingsData,
    ) -> StandingsImportResult:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        if not standings_data.rows:
            raise ValueError(
                "Die Tabelle enthält keine Mannschaften."
            )

        competition = self.competition_repository.get(
            competition_id
        )

        if competition is None:
            raise ValueError(
                "Der Wettbewerb wurde nicht gefunden."
            )

        team_lookup = self._build_team_lookup(
            competition_id
        )

        imported = 0
        updated = 0
        unmatched_teams: list[str] = []

        try:
            self.connection.execute(
                "BEGIN"
            )

            for row in standings_data.rows:
                team_id = self._find_team_id(
                    row=row,
                    team_lookup=team_lookup,
                )

                if team_id is None:
                    unmatched_teams.append(
                        row.team_name
                    )
                    continue

                existing = (
                    self.standing_repository
                    .get_by_competition_and_team(
                        competition_id=competition_id,
                        team_id=team_id,
                    )
                )

                self.standing_repository.upsert(
                    competition_id=competition_id,
                    team_id=team_id,
                    position=row.position,
                    played=row.played,
                    wins=row.wins,
                    draws=row.draws,
                    losses=row.losses,
                    goals_for=row.goals_for,
                    goals_against=row.goals_against,
                    points=row.points,
                    source="fussball.de",
                    commit=False,
                )

                if existing is None:
                    imported += 1
                else:
                    updated += 1

            if unmatched_teams:
                missing = ", ".join(
                    unmatched_teams
                )

                raise ValueError(
                    "Folgende Tabellenmannschaften konnten "
                    "keiner Mannschaft im Wettbewerb zugeordnet "
                    f"werden: {missing}"
                )

            self.connection.commit()

        except (sqlite3.Error, ValueError):
            self.connection.rollback()
            raise

        return StandingsImportResult(
            rows_imported=imported,
            rows_updated=updated,
            unmatched_teams=tuple(
                unmatched_teams
            ),
        )

    def _build_team_lookup(
        self,
        competition_id: int,
    ) -> dict[str, set[int]]:
        rows = (
            self.competition_repository
            .get_competition_teams(
                competition_id
            )
        )

        if not rows:
            raise ValueError(
                "Dem Wettbewerb sind keine Mannschaften "
                "zugeordnet."
            )

        lookup: dict[str, set[int]] = {}

        for row in rows:
            team_id = int(row[0])
            club_name = str(row[1] or "")
            team_name = str(row[2] or "")
            short_name = str(row[3] or "")

            names = {
                team_name,
                short_name,
                club_name,
            }

            for name in names:
                normalized = self._normalize_name(
                    name
                )

                if not normalized:
                    continue

                lookup.setdefault(
                    normalized,
                    set(),
                ).add(team_id)

        return lookup

    def _find_team_id(
        self,
        row: StandingRow,
        team_lookup: dict[str, set[int]],
    ) -> int | None:
        candidates = self._team_name_candidates(
            row.team_name
        )

        matches: set[int] = set()

        for candidate in candidates:
            matches.update(
                team_lookup.get(
                    candidate,
                    set(),
                )
            )

        if len(matches) == 1:
            return next(
                iter(matches)
            )

        if len(matches) > 1:
            raise ValueError(
                "Die Tabellenmannschaft ist nicht eindeutig: "
                f"{row.team_name}"
            )

        return None

    def _team_name_candidates(
        self,
        team_name: str,
    ) -> set[str]:
        normalized = self._normalize_name(
            team_name
        )

        candidates = {
            normalized,
        }

        replacements = (
            ("spielgemeinschaft", "sg"),
            ("sportverein", "sv"),
            ("fußballclub", "fc"),
            ("fussballclub", "fc"),
        )

        for old, new in replacements:
            if old in normalized:
                candidates.add(
                    normalized.replace(
                        old,
                        new,
                    )
                )

        return {
            candidate
            for candidate in candidates
            if candidate
        }

    def _normalize_name(
        self,
        value: str,
    ) -> str:
        normalized = value.strip().casefold()
        normalized = normalized.replace(
            "ß",
            "ss",
        )
        normalized = self.WHITESPACE_PATTERN.sub(
            " ",
            normalized,
        )
        normalized = self.PUNCTUATION_PATTERN.sub(
            "",
            normalized,
        )

        return normalized
