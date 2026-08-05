from __future__ import annotations

import re
from datetime import date, datetime

from src.database.models.association import Association
from src.database.models.league import League
from src.database.models.match import Match
from src.database.models.season import Season
from src.database.repositories.association_repository import (
    AssociationRepository,
)
from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import (
    CompetitionRepository,
)
from src.database.repositories.league_repository import LeagueRepository
from src.database.repositories.match_repository import MatchRepository
from src.database.repositories.season_repository import SeasonRepository
from src.database.repositories.team_repository import TeamRepository
from src.importer.fussballde.parsers.schedule_data import (
    ScheduleData,
    ScheduleMatch,
)
from src.importer.fussballde.parsers.schedule_parser import ScheduleParser
from src.services.imports.import_result import ImportResult


class ScheduleImportService:

    TEAM_SUFFIX_PATTERN = re.compile(
        r"\s+(I{1,4}|V|VI|[2-9]\.?)$",
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

    SEASON_PATTERN = re.compile(
        r"\b(20\d{2})\s*[/\-]\s*(20\d{2}|\d{2})\b"
    )

    def __init__(
        self,
        association_repository: AssociationRepository,
        league_repository: LeagueRepository,
        season_repository: SeasonRepository,
        club_repository: ClubRepository,
        team_repository: TeamRepository,
        competition_repository: CompetitionRepository,
        match_repository: MatchRepository,
    ) -> None:
        self.association_repository = association_repository
        self.league_repository = league_repository
        self.season_repository = season_repository
        self.club_repository = club_repository
        self.team_repository = team_repository
        self.competition_repository = competition_repository
        self.match_repository = match_repository

    def import_schedule(
        self,
        parser: ScheduleParser,
    ) -> ImportResult:
        schedule_data = parser.parse()

        if not schedule_data.matches:
            raise ValueError(
                "Der Spielplan enthält keine Spiele."
            )

        self._complete_schedule_data(schedule_data)

        result = ImportResult()

        association_id = self._import_association(
            schedule_data
        )

        league_id = self._import_league(
            schedule_data=schedule_data,
            association_id=association_id,
        )

        season_id = self._import_season(
            schedule_data
        )

        competition_id = self._import_competition(
            schedule_data=schedule_data,
            league_id=league_id,
            season_id=season_id,
            result=result,
        )

        self._import_clubs(
            matches=schedule_data.matches,
            association_id=association_id,
            result=result,
        )

        team_ids = self._import_teams(
            matches=schedule_data.matches,
            competition_id=competition_id,
            result=result,
        )

        self._import_matches(
            matches=schedule_data.matches,
            team_ids=team_ids,
            competition_id=competition_id,
            league_id=league_id,
            season_id=season_id,
            result=result,
        )

        return result

    def _complete_schedule_data(
        self,
        schedule_data: ScheduleData,
    ) -> None:
        schedule_data.league_name = (
            schedule_data.league_name.strip()
            or schedule_data.competition_name.strip()
            or self._get_competition_name(
                schedule_data.matches
            )
        )

        schedule_data.competition_name = (
            schedule_data.competition_name.strip()
            or self._get_competition_name(
                schedule_data.matches
            )
        )

        schedule_data.category = (
            schedule_data.category.strip()
            or self._get_category(
                schedule_data.matches
            )
        )

        schedule_data.season_name = (
            schedule_data.season_name.strip()
            or self._derive_season_name(
                schedule_data
            )
        )

        schedule_data.association_name = (
            schedule_data.association_name.strip()
            or "Unbekannter Verband"
        )

        if not schedule_data.league_name:
            raise ValueError(
                "Der Liganame konnte nicht ermittelt werden."
            )

        if not schedule_data.competition_name:
            raise ValueError(
                "Der Wettbewerbsname konnte nicht ermittelt werden."
            )

        if not schedule_data.season_name:
            raise ValueError(
                "Die Saison konnte nicht ermittelt werden."
            )

    def _import_association(
        self,
        schedule_data: ScheduleData,
    ) -> int:
        return self.association_repository.get_or_create(
            Association(
                name=schedule_data.association_name,
            )
        )

    def _import_league(
        self,
        schedule_data: ScheduleData,
        association_id: int,
    ) -> int:
        return self.league_repository.get_or_create(
            League(
                association_id=association_id,
                name=schedule_data.league_name,
                level=1,
                season_type="Liga",
                active=True,
            )
        )

    def _import_season(
        self,
        schedule_data: ScheduleData,
    ) -> int:
        start_date, end_date = self._season_dates(
            schedule_data.season_name
        )

        return self.season_repository.get_or_create(
            Season(
                name=schedule_data.season_name,
                start_date=start_date,
                end_date=end_date,
                external_id=None,
                active=True,
            )
        )

    def _import_competition(
        self,
        schedule_data: ScheduleData,
        league_id: int,
        season_id: int,
        result: ImportResult,
    ) -> int:
        existing_competition = (
            self.competition_repository.get_by_name(
                league_id=league_id,
                season_id=season_id,
                name=schedule_data.competition_name,
            )
        )

        if existing_competition is not None:
            if existing_competition.competition_id is None:
                raise ValueError(
                    "Der vorhandene Wettbewerb besitzt keine ID."
                )

            return int(existing_competition.competition_id)

        competition_id = (
            self.competition_repository.get_or_create(
                league_id=league_id,
                season_id=season_id,
                name=schedule_data.competition_name,
                active=True,
            )
        )

        result.competitions_created += 1

        return competition_id

    def _import_clubs(
        self,
        matches: list[ScheduleMatch],
        association_id: int,
        result: ImportResult,
    ) -> None:
        club_names = {
            self._extract_club_name(team_name)
            for team_name in self._get_team_names(matches)
        }

        for club_name in sorted(
            club_names,
            key=str.casefold,
        ):
            if self.club_repository.get_by_name(
                club_name
            ) is not None:
                continue

            self.club_repository.get_or_create(
                name=club_name,
                association_id=association_id,
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

        team_names = self._get_team_names(matches)
        age_group = self._get_category(matches)
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

            club_id = int(club["club_id"])

            existing_team = self.team_repository.get_by_name(
                club_id=club_id,
                name=team_name,
            )

            if existing_team is not None:
                team_id = int(existing_team["team_id"])
            else:
                team_id = self.team_repository.get_or_create(
                    club_id=club_id,
                    name=team_name,
                    team_number=self._extract_team_number(
                        team_name
                    ),
                    age_group=age_group,
                )

                result.teams_created += 1

            self.competition_repository.add_team(
                competition_id=competition_id,
                team_id=team_id,
            )

            team_ids[
                self._normalize_team_key(team_name)
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
        for schedule_match in matches:
            home_team_id = team_ids.get(
                self._normalize_team_key(
                    schedule_match.home_team
                )
            )

            away_team_id = team_ids.get(
                self._normalize_team_key(
                    schedule_match.away_team
                )
            )

            if home_team_id is None:
                raise ValueError(
                    "Heimmannschaft wurde nicht gefunden: "
                    f"{schedule_match.home_team}"
                )

            if away_team_id is None:
                raise ValueError(
                    "Auswärtsmannschaft wurde nicht gefunden: "
                    f"{schedule_match.away_team}"
                )

            database_match = Match(
                competition_id=competition_id,
                season_id=season_id,
                league_id=league_id,
                matchday=schedule_match.matchday,
                match_date=schedule_match.date or None,
                kickoff_time=schedule_match.time or None,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_goals=schedule_match.home_score,
                away_goals=schedule_match.away_score,
                status=(
                    schedule_match.status.strip()
                    or "scheduled"
                ),
                notes=(
                    "fussball.de: "
                    f"{schedule_match.match_url}"
                ),
                external_id=schedule_match.match_id,
                home_team_name=schedule_match.home_team,
                away_team_name=schedule_match.away_team,
            )

            _, created = self.match_repository.upsert(
                database_match
            )

            if created:
                result.matches_created += 1
            else:
                result.matches_updated += 1

    def _derive_season_name(
        self,
        schedule_data: ScheduleData,
    ) -> str:
        for value in (
            schedule_data.competition_name,
            schedule_data.league_name,
        ):
            match = self.SEASON_PATTERN.search(value)

            if match:
                start_year = int(match.group(1))
                end_year_text = match.group(2)
                end_year = (
                    int(end_year_text)
                    if len(end_year_text) == 4
                    else (start_year // 100) * 100
                    + int(end_year_text)
                )

                return f"{start_year}/{str(end_year)[-2:]}"

        match_dates = [
            parsed_date
            for parsed_date in (
                self._parse_iso_date(match.date)
                for match in schedule_data.matches
            )
            if parsed_date is not None
        ]

        if not match_dates:
            return ""

        earliest = min(match_dates)

        if earliest.month >= 7:
            start_year = earliest.year
        else:
            start_year = earliest.year - 1

        return f"{start_year}/{str(start_year + 1)[-2:]}"

    @classmethod
    def _season_dates(
        cls,
        season_name: str,
    ) -> tuple[str | None, str | None]:
        match = cls.SEASON_PATTERN.search(
            season_name
        )

        if not match:
            return None, None

        start_year = int(match.group(1))
        end_year_text = match.group(2)
        end_year = (
            int(end_year_text)
            if len(end_year_text) == 4
            else (start_year // 100) * 100
            + int(end_year_text)
        )

        return (
            date(start_year, 7, 1).isoformat(),
            date(end_year, 6, 30).isoformat(),
        )

    @staticmethod
    def _parse_iso_date(
        value: str,
    ) -> date | None:
        if not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            return None

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
            return ""

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

    @staticmethod
    def _normalize_team_key(
        team_name: str,
    ) -> str:
        return " ".join(
            team_name.split()
        ).casefold()

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
            return cls.ROMAN_TEAM_NUMBERS[suffix]

        if suffix.isdigit():
            return int(suffix)

        return 1
