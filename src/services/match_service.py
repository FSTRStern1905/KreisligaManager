from src.database.models.match import Match
from src.database.repositories.match_repository import MatchRepository


class MatchService:
    VALID_STATUSES = {
        "scheduled",
        "live",
        "finished",
        "postponed",
        "cancelled",
        "abandoned",
    }

    def __init__(self, repository: MatchRepository):
        self.repository = repository

    def get_match(self, match_id: int) -> Match | None:
        return self.repository.get_by_id(match_id)

    def get_matches_by_competition(
        self,
        competition_id: int,
    ) -> list[Match]:
        return self.repository.get_by_competition(
            competition_id
        )

    def update_match(
        self,
        match_id: int,
        home_goals: int | None,
        away_goals: int | None,
        match_date: str | None,
        kickoff_time: str | None,
        attendance: int | None,
        stadium_id: int | None,
        referee_id: int | None,
        status: str,
        notes: str,
    ):
        match = self.repository.get_by_id(match_id)

        if match is None:
            raise ValueError("Das Spiel wurde nicht gefunden.")

        clean_status = status.strip().lower()

        if clean_status not in self.VALID_STATUSES:
            raise ValueError("Ungültiger Spielstatus.")

        if home_goals is not None and home_goals < 0:
            raise ValueError("Heimtore dürfen nicht negativ sein.")

        if away_goals is not None and away_goals < 0:
            raise ValueError("Auswärtstore dürfen nicht negativ sein.")

        if attendance is not None and attendance < 0:
            raise ValueError("Zuschauerzahl darf nicht negativ sein.")

        if clean_status == "finished":
            if home_goals is None or away_goals is None:
                raise ValueError(
                    "Bei einem beendeten Spiel muss ein Ergebnis vorhanden sein."
                )

        match.home_goals = home_goals
        match.away_goals = away_goals
        match.match_date = self._clean_optional_text(match_date)
        match.kickoff_time = self._clean_optional_text(kickoff_time)
        match.attendance = attendance
        match.stadium_id = stadium_id
        match.referee_id = referee_id
        match.status = clean_status
        match.notes = notes.strip()

        self.repository.update(match)

    def delete_match(self, match_id: int):
        match = self.repository.get_by_id(match_id)

        if match is None:
            raise ValueError("Das Spiel wurde nicht gefunden.")

        self.repository.delete(match_id)

    def _clean_optional_text(
        self,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        clean_value = value.strip()

        if not clean_value:
            return None

        return clean_value