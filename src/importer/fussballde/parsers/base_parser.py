from abc import ABC, abstractmethod
from typing import Any

from playwright.sync_api import Page


class BaseParser(ABC):
    """
    Basisklasse für alle fussball.de-Parser.
    """

    def __init__(self, page: Page):
        self.page = page

    @abstractmethod
    def parse(self) -> Any:
        """
        Liest Daten aus der geladenen Seite aus.
        """
        raise NotImplementedError

    @staticmethod
    def clean_text(value: str | None) -> str:
        """
        Entfernt unnötige Leerzeichen und Zeilenumbrüche.
        """
        if value is None:
            return ""

        return " ".join(value.split())

    @staticmethod
    def parse_score(value: str) -> tuple[int | None, int | None]:
        """
        Wandelt ein Ergebnis wie '3:2' in zwei Zahlen um.

        Noch nicht gespielte Spiele liefern:
        (None, None)
        """
        cleaned_value = BaseParser.clean_text(value)

        if not cleaned_value or cleaned_value == ":":
            return None, None

        parts = cleaned_value.split(":")

        if len(parts) != 2:
            return None, None

        try:
            home_score = int(parts[0].strip())
            away_score = int(parts[1].strip())
        except ValueError:
            return None, None

        return home_score, away_score