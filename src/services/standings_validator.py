from dataclasses import dataclass, field

from src.database.repositories.match_repository import MatchRepository
from src.database.repositories.standing_repository import StandingRepository


@dataclass(slots=True)
class CalculatedStanding:
    team_id: int
    team_name: str = ""

    position: int = 0
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0


@dataclass(slots=True)
class StandingDifference:
    team_id: int
    team_name: str
    field_name: str
    official_value: int
    calculated_value: int


@dataclass(slots=True)
class StandingsValidationResult:
    competition_id: int

    official_team_count: int = 0
    calculated_team_count: int = 0
    finished_match_count: int = 0

    differences: list[StandingDifference] = field(
        default_factory=list
    )
    missing_in_official: list[CalculatedStanding] = field(
        default_factory=list
    )
    missing_in_calculated: list[dict] = field(
        default_factory=list
    )

    @property
    def is_valid(self) -> bool:
        return (
            not self.differences
            and not self.missing_in_official
            and not self.missing_in_calculated
        )

    @property
    def difference_count(self) -> int:
        return len(self.differences)

    def to_text(self) -> str:
        lines = [
            "Tabellenprüfung",
            "================",
            f"Wettbewerb: {self.competition_id}",
            (
                "Offizielle Mannschaften: "
                f"{self.official_team_count}"
            ),
            (
                "Berechnete Mannschaften: "
                f"{self.calculated_team_count}"
            ),
            (
                "Gewertete Spiele: "
                f"{self.finished_match_count}"
            ),
            "",
        ]

        if self.is_valid:
            lines.append(
                "Ergebnis: Die berechnete Tabelle stimmt "
                "mit der offiziellen Tabelle überein."
            )

            return "\n".join(lines)

        lines.append(
            "Ergebnis: Es wurden Abweichungen gefunden."
        )
        lines.append("")

        if self.differences:
            lines.append("Unterschiede:")
            lines.append("------------")

            for difference in self.differences:
                lines.append(
                    f"{difference.team_name} – "
                    f"{difference.field_name}: "
                    f"offiziell {difference.official_value}, "
                    f"berechnet {difference.calculated_value}"
                )

            lines.append("")

        if self.missing_in_official:
            lines.append(
                "Nur in der berechneten Tabelle:"
            )
            lines.append("---------------------------")

            for standing in self.missing_in_official:
                lines.append(
                    f"{standing.team_name} "
                    f"(Team-ID: {standing.team_id})"
                )

            lines.append("")

        if self.missing_in_calculated:
            lines.append(
                "Nur in der offiziellen Tabelle:"
            )
            lines.append("--------------------------")

            for standing in self.missing_in_calculated:
                team_name = (
                    standing.get("team_name")
                    or standing.get("team_short_name")
                    or f"Team-ID {standing['team_id']}"
                )

                lines.append(
                    f"{team_name} "
                    f"(Team-ID: {standing['team_id']})"
                )

        return "\n".join(lines)


class StandingsValidator:

    COMPARISON_FIELDS = {
        "position": "Tabellenplatz",
        "played": "Spiele",
        "wins": "Siege",
        "draws": "Unentschieden",
        "losses": "Niederlagen",
        "goals_for": "Tore",
        "goals_against": "Gegentore",
        "goal_difference": "Tordifferenz",
        "points": "Punkte",
    }

    def __init__(
        self,
        match_repository: MatchRepository,
        standing_repository: StandingRepository,
    ):
        self.match_repository = match_repository
        self.standing_repository = standing_repository

    def validate(
        self,
        competition_id: int,
    ) -> StandingsValidationResult:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        official_standings = (
            self.standing_repository.get_by_competition(
                competition_id
            )
        )

        calculated_standings = self.calculate(
            competition_id
        )

        result = StandingsValidationResult(
            competition_id=competition_id,
            official_team_count=len(
                official_standings
            ),
            calculated_team_count=len(
                calculated_standings
            ),
            finished_match_count=(
                self.match_repository.get_finished_match_count(
                    competition_id
                )
            ),
        )

        official_by_team_id = {
            int(standing["team_id"]): standing
            for standing in official_standings
        }

        calculated_by_team_id = {
            standing.team_id: standing
            for standing in calculated_standings
        }

        for team_id, calculated in (
            calculated_by_team_id.items()
        ):
            official = official_by_team_id.get(team_id)

            if official is None:
                result.missing_in_official.append(
                    calculated
                )
                continue

            self._compare_standing(
                official=official,
                calculated=calculated,
                result=result,
            )

        for team_id, official in (
            official_by_team_id.items()
        ):
            if team_id not in calculated_by_team_id:
                result.missing_in_calculated.append(
                    official
                )

        return result

    def calculate(
        self,
        competition_id: int,
    ) -> list[CalculatedStanding]:
        if competition_id <= 0:
            raise ValueError(
                "Ungültige Wettbewerbs-ID."
            )

        matches = (
            self.match_repository.get_by_competition(
                competition_id
            )
        )

        standings_by_team_id: dict[
            int,
            CalculatedStanding,
        ] = {}

        for match in matches:
            if not match.is_finished:
                continue

            if (
                match.home_team_id is None
                or match.away_team_id is None
                or match.home_goals is None
                or match.away_goals is None
            ):
                continue

            home_standing = self._get_or_create_team(
                standings_by_team_id=standings_by_team_id,
                team_id=match.home_team_id,
                team_name=match.home_team_name,
            )

            away_standing = self._get_or_create_team(
                standings_by_team_id=standings_by_team_id,
                team_id=match.away_team_id,
                team_name=match.away_team_name,
            )

            home_standing.played += 1
            away_standing.played += 1

            home_standing.goals_for += (
                match.home_goals
            )
            home_standing.goals_against += (
                match.away_goals
            )

            away_standing.goals_for += (
                match.away_goals
            )
            away_standing.goals_against += (
                match.home_goals
            )

            if match.home_goals > match.away_goals:
                home_standing.wins += 1
                home_standing.points += 3
                away_standing.losses += 1

            elif match.home_goals < match.away_goals:
                away_standing.wins += 1
                away_standing.points += 3
                home_standing.losses += 1

            else:
                home_standing.draws += 1
                away_standing.draws += 1

                home_standing.points += 1
                away_standing.points += 1

        calculated_standings = list(
            standings_by_team_id.values()
        )

        for standing in calculated_standings:
            standing.goal_difference = (
                standing.goals_for
                - standing.goals_against
            )

        calculated_standings.sort(
            key=lambda standing: (
                -standing.points,
                -standing.goal_difference,
                -standing.goals_for,
                standing.goals_against,
                standing.team_name.casefold(),
                standing.team_id,
            )
        )

        for position, standing in enumerate(
            calculated_standings,
            start=1,
        ):
            standing.position = position

        return calculated_standings

    @staticmethod
    def _get_or_create_team(
        standings_by_team_id: dict[
            int,
            CalculatedStanding,
        ],
        team_id: int,
        team_name: str,
    ) -> CalculatedStanding:
        standing = standings_by_team_id.get(team_id)

        if standing is None:
            standing = CalculatedStanding(
                team_id=team_id,
                team_name=team_name.strip(),
            )

            standings_by_team_id[team_id] = (
                standing
            )

        elif (
            not standing.team_name
            and team_name.strip()
        ):
            standing.team_name = team_name.strip()

        return standing

    def _compare_standing(
        self,
        official: dict,
        calculated: CalculatedStanding,
        result: StandingsValidationResult,
    ) -> None:
        team_name = (
            official.get("team_name")
            or official.get("team_short_name")
            or calculated.team_name
            or f"Team-ID {calculated.team_id}"
        )

        for attribute_name, display_name in (
            self.COMPARISON_FIELDS.items()
        ):
            official_value = int(
                official[attribute_name]
            )

            calculated_value = int(
                getattr(
                    calculated,
                    attribute_name,
                )
            )

            if official_value == calculated_value:
                continue

            result.differences.append(
                StandingDifference(
                    team_id=calculated.team_id,
                    team_name=team_name,
                    field_name=display_name,
                    official_value=official_value,
                    calculated_value=calculated_value,
                )
            )