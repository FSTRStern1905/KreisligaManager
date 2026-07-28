from __future__ import annotations

from bs4 import BeautifulSoup, Tag


class MatchHtmlDocument:

    def __init__(self, html: str):
        self.soup = BeautifulSoup(
            html,
            "html.parser",
        )

    def select_one(
        self,
        selector: str,
    ) -> Tag | None:
        return self.soup.select_one(selector)

    def select(
        self,
        selector: str,
    ) -> list[Tag]:
        return self.soup.select(selector)

    def get_text(self) -> str:
        return self.soup.get_text(
            " ",
            strip=True,
        )

    def __getattr__(self, item):
        return getattr(
            self.soup,
            item,
        )