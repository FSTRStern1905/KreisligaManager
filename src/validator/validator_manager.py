from __future__ import annotations

from src.validator.match_validator import MatchValidator


class ValidatorManager:
    """
    Zentrale Verwaltung aller Validatoren.

    Aktuell:
    - MatchValidator

    Später:
    - PlayerValidator
    - EventValidator
    - LineupValidator
    - RefereeValidator
    - StadiumValidator
    """

    def __init__(self) -> None:
        self.match_validator = MatchValidator()

    def validate_match(
        self,
        html_document,
        database_data,
    ):
        return self.match_validator.validate(
            html_document=html_document,
            database_data=database_data,
        )