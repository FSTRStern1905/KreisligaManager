from __future__ import annotations

from src.importer.fussballde.browser import (
    FussballDeBrowser,
)
from src.importer.fussballde.parsers.schedule_parser import (
    ScheduleParser,
)
from src.services.imports.import_result import (
    ImportResult,
)
from src.services.imports.schedule_import_service import (
    ScheduleImportService,
)


class FussballDeImporter:

    def __init__(
        self,
        import_service: ScheduleImportService,
    ) -> None:
        self.import_service = import_service

    def import_schedule(
        self,
        url: str,
        league_id: int,
        season_id: int,
        headless: bool = True,
    ) -> ImportResult:
        browser = FussballDeBrowser()

        try:
            browser.start(
                headless=headless,
            )

            browser.open(url)

            if browser.page is None:
                raise RuntimeError(
                    "Die fussball.de-Seite wurde nicht geladen."
                )

            parser = ScheduleParser(
                browser.page,
            )

            return self.import_service.import_schedule(
                parser=parser,
                league_id=league_id,
                season_id=season_id,
            )

        finally:
            browser.close()