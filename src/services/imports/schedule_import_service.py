from __future__ import annotations

import re

from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.match_repository import MatchRepository
from src.database.repositories.team_repository import TeamRepository
from src.importer.fussballde.parsers.schedule_parser import (
    ScheduleMatch,
    ScheduleParser,
)
from src.services.imports.import_result import ImportResult


class ScheduleImportService:

    TEAM_SUFFIX_PATTERN = re.compile(
        r"\s+(I{1,4}|V|VI|[2-9]\.?|[2-9])$",
        re.IGNORECASE,
    )

    ROMAN_TEAM_NUMBERS = {
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
    }

    def __init__(
        self,
        club_repository: ClubRepository,
        team_repository: TeamRepository,
        competition_repository: CompetitionRepository,
        match_repository: MatchRepository,
    ) -> None:
        self.club_repository = club_repository
        self.team_repository = team_repository
        self.competition_repository = competition_repository
        self.match_repository = match_repository

    def import_schedule(
        self,
        parser: ScheduleParser,
        league_id: int,
        season_id: int,
    ) -> ImportResult:
        if league_id <= 0:
            raise ValueError(
                "Ungültige Liga-ID."
            )

        if season_id <= 0:
            raise ValueError(
                "Ungültige Saison-ID."
            )

        matches = parser.parse()

        if not matches:
            raise ValueError(
                "Der Spielplan enthält keine Spiele."
            )

        result = ImportResult()

        competition_id = self._import_competition(
            matches=matches,
            league_id=league_id,
            season_id=season_id,
            result=result,
        )

        self._import_clubs(
            matches=matches,
            result=result,
        )

        team_ids = self._import_teams(
            matches=matches,
            competition_id=competition_id,
            result=result,
        )

        self._import_matches(
            matches=matches,
            team_ids=team_ids,
            competition_id=competition_id,
            league_id=league_id,
            season_id=season_id,
            result=result,
        )

        return result

    def _import_competition(
        self,
        matches: list[ScheduleMatch],
        league_id: int,
        season_id: int,
        result: ImportResult,
    ) -> int:
        competition_name = self._get_competition_name(
            matches
        )

        existing_competition = (
            self.competition_repository.get_by_name(
                league_id=league_id,
                season_id=season_id,
                name=competition_name,
            )
        )

        if existing_competition is not None:
            if existing_competition.competition_id is None:
                raise ValueError(
                    "Der vorhandene Wettbewerb besitzt keine ID."
                )

            return existing_competition.competition_id

        competition_id = (
            self.competition_repository.get_or_create(
                league_id=league_id,
                season_id=season_id,
                name=competition_name,
                active=True,
            )
        )

        result.competitions_created += 1

        return competition_id

    def _import_clubs(
        self,
        matches: list[ScheduleMatch],
        result: ImportResult,
    ) -> None:
        team_names = self._get_team_names(
            matches
        )

        club_names = {
            self._extract_club_name(team_name)
            for team_name in team_names
        }

        for club_name in sorted(
            club_names,
            key=str.casefold,
        ):
            existing_club = (
                self.club_repository.get_by_name(
                    club_name
                )
            )

            if existing_club is not None:
                continue

            self.club_repository.get_or_create(
                name=club_name,
            )

            result.clubs_created += 1

    def _import_teams(
        self,
        matches: list[ScheduleMatch],
        competition_id: int,
        result: ImportResult,
    ) -> dict[str, int]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        team_names = self._get_team_names(
            matches
        )

        age_group = self._get_category(
            matches
        )

        team_ids: dict[str, int] = {}

        for team_name in sorted(
            team_names,
            key=str.casefold,
        ):
            club_name = self._extract_club_name(
                team_name
            )

            club = self.club_repository.get_by_name(
                club_name
            )

            if club is None:
                raise ValueError(
                    "Verein wurde nicht gefunden: "
                    f"{club_name}"
                )

            club_id = int(
                club["club_id"]
            )

            existing_team = (
                self.team_repository.get_by_name(
                    club_id=club_id,
                    name=team_name,
                )
            )

            if existing_team is not None:
                team_id = int(
                    existing_team["team_id"]
                )

            else:
                team_id = (
                    self.team_repository.get_or_create(
                        club_id=club_id,
                        name=team_name,
                        team_number=(
                            self._extract_team_number(
                                team_name
                            )
                        ),
                        age_group=age_group,
                    )
                )

                result.teams_created += 1

            self.competition_repository.add_team(
                competition_id=competition_id,
                team_id=team_id,
            )

            team_ids[
                team_name.casefold()
            ] = team_id

        return team_ids

    def _import_matches(
        self,
        matches: list[ScheduleMatch],
        team_ids: dict[str, int],
        competition_id: int,
        league_id: int,
        season_id: int,
        result: ImportResult,
    ) -> None:
        pass

    @staticmethod
    def _get_competition_name(
        matches: list[ScheduleMatch],
    ) -> str:
        competition_names = {
            match.competition.strip()
            for match in matches
            if match.competition.strip()
        }

        if not competition_names:
            raise ValueError(
                "Der Wettbewerbsname konnte nicht ermittelt werden."
            )

        if len(competition_names) > 1:
            names = ", ".join(
                sorted(competition_names)
            )

            raise ValueError(
                "Der Spielplan enthält mehrere Wettbewerbe: "
                f"{names}"
            )

        return competition_names.pop()

    @staticmethod
    def _get_category(
        matches: list[ScheduleMatch],
    ) -> str:
        categories = {
            match.category.strip()
            for match in matches
            if match.category.strip()
        }

        if not categories:
            return ""

        return sorted(
            categories,
            key=str.casefold,
        )[0]

    @staticmethod
    def _get_team_names(
        matches: list[ScheduleMatch],
    ) -> set[str]:
        team_names: set[str] = set()

        for match in matches:
            home_team = " ".join(
                match.home_team.split()
            )

            away_team = " ".join(
                match.away_team.split()
            )

            if home_team:
                team_names.add(home_team)

            if away_team:
                team_names.add(away_team)

        if not team_names:
            raise ValueError(
                "Es konnten keine Mannschaften ermittelt werden."
            )

        return team_names

    @classmethod
    def _extract_club_name(
        cls,
        team_name: str,
    ) -> str:
        normalized_name = " ".join(
            team_name.split()
        )

        club_name = cls.TEAM_SUFFIX_PATTERN.sub(
            "",
            normalized_name,
        ).strip()

        if not club_name:
            raise ValueError(
                "Der Vereinsname konnte nicht ermittelt werden: "
                f"{team_name}"
            )

        return club_name

    @classmethod
    def _extract_team_number(
        cls,
        team_name: str,
    ) -> int:
        normalized_name = " ".join(
            team_name.split()
        )

        match = cls.TEAM_SUFFIX_PATTERN.search(
            normalized_name
        )

        if match is None:
            return 1

        suffix = (
            match.group(1)
            .upper()
            .rstrip(".")
        )

        if suffix in cls.ROMAN_TEAM_NUMBERS:
            return cls.ROMAN_TEAM_NUMBERS[
                suffix
            ]

        if suffix.isdigit():
            return int(suffix)

        return 1