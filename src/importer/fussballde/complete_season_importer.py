from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from typing import Any

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.match_detail_importer import (
    MatchDetailImporter,
)
from src.importer.fussballde.parsers.schedule_parser import (
    ScheduleParser,
)
from src.services.imports.schedule_import_service import (
    ScheduleImportService,
)


@dataclass(slots=True)
class CompleteSeasonImportResult:
    schedule_result: Any = None
    matches_found: int = 0
    match_details_imported: int = 0
    match_details_failed: int = 0
    players_imported: int = 0
    events_imported: int = 0
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        result = asdict(self)

        schedule_result = self.schedule_result

        if schedule_result is None:
            result["schedule_result"] = None
        elif hasattr(schedule_result, "__dict__"):
            result["schedule_result"] = dict(
                schedule_result.__dict__
            )
        else:
            result["schedule_result"] = str(
                schedule_result
            )

        return result


class ParsedScheduleAdapter:
    """
    Übergibt bereits geparste Spielplandaten erneut an den
    ScheduleImportService, ohne die Webseite ein zweites Mal
    parsen zu müssen.
    """

    def __init__(
        self,
        parsed_schedule: Any,
    ) -> None:
        self.parsed_schedule = parsed_schedule

    def parse(self) -> Any:
        return self.parsed_schedule


class CompleteSeasonImporter:
    def __init__(
        self,
        connection: sqlite3.Connection,
        schedule_import_service: ScheduleImportService,
    ) -> None:
        self.connection = connection
        self.schedule_import_service = (
            schedule_import_service
        )

        self.match_detail_importer = (
            MatchDetailImporter(
                connection=connection,
            )
        )

    def import_competition(
        self,
        url: str,
        headless: bool = True,
        continue_on_detail_error: bool = True,
        max_detail_matches: int | None = None,
    ) -> CompleteSeasonImportResult:
        normalized_url = url.strip()

        if not normalized_url:
            raise ValueError(
                "Die Wettbewerbs-URL darf nicht leer sein."
            )

        if (
            max_detail_matches is not None
            and max_detail_matches < 1
        ):
            raise ValueError(
                "max_detail_matches muss mindestens 1 sein "
                "oder None."
            )

        browser = FussballDeBrowser()
        errors: list[str] = []

        result = CompleteSeasonImportResult()

        try:
            browser.start(
                headless=headless,
            )

            browser.open(
                normalized_url
            )

            if browser.page is None:
                raise RuntimeError(
                    "Die fussball.de-Seite wurde "
                    "nicht geladen."
                )

            schedule_parser = ScheduleParser(
                browser.page
            )

            parsed_schedule = (
                schedule_parser.parse()
            )

            schedule_matches = (
                self._get_schedule_matches(
                    parsed_schedule
                )
            )

            if not schedule_matches:
                raise ValueError(
                    "Im Spielplan wurden keine "
                    "Spiele gefunden."
                )

            result.matches_found = len(
                schedule_matches
            )

            parser_adapter = (
                ParsedScheduleAdapter(
                    parsed_schedule
                )
            )

            result.schedule_result = (
                self.schedule_import_service
                .import_schedule(
                    parser=parser_adapter,
                )
            )

            detail_matches = schedule_matches

            if max_detail_matches is not None:
                detail_matches = schedule_matches[
                    :max_detail_matches
                ]

            print(
                "Detailspiele für diesen Lauf: "
                f"{len(detail_matches)} von "
                f"{len(schedule_matches)}"
            )

            for index, schedule_match in enumerate(
                detail_matches,
                start=1,
            ):
                match_url = self._get_value(
                    schedule_match,
                    "match_url",
                    "",
                )

                external_id = self._get_value(
                    schedule_match,
                    "match_id",
                    "",
                )

                if not match_url:
                    errors.append(
                        "Keine Spiel-URL vorhanden: "
                        f"{external_id or index}"
                    )

                    result.match_details_failed += 1
                    continue

                print(
                    f"[{index}/{len(detail_matches)}] "
                    f"Importiere Spiel: {match_url}"
                )

                try:
                    detail_result = (
                        self.match_detail_importer
                        .import_from_page(
                            page=browser.page,
                            source_url=match_url,
                        )
                    )

                    result.match_details_imported += 1

                    result.players_imported += int(
                        detail_result.get(
                            "players_imported",
                            0,
                        )
                    )

                    result.events_imported += int(
                        detail_result.get(
                            "events_imported",
                            0,
                        )
                    )

                except Exception as error:
                    result.match_details_failed += 1

                    error_message = (
                        f"{external_id or match_url}: "
                        f"{error}"
                    )

                    errors.append(
                        error_message
                    )

                    print(
                        "Detailimport fehlgeschlagen: "
                        f"{error_message}"
                    )

                    if not continue_on_detail_error:
                        raise

            result.errors = tuple(
                errors
            )

            return result

        except Exception:
            self.connection.rollback()
            raise

        finally:
            browser.close()

    @staticmethod
    def _get_schedule_matches(
        parsed_schedule: Any,
    ) -> list[Any]:
        if parsed_schedule is None:
            return []

        if isinstance(
            parsed_schedule,
            list,
        ):
            return parsed_schedule

        matches = getattr(
            parsed_schedule,
            "matches",
            None,
        )

        if matches is None:
            return []

        return list(
            matches
        )

    @staticmethod
    def _get_value(
        source: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        if isinstance(source, dict):
            return source.get(
                name,
                default,
            )

        return getattr(
            source,
            name,
            default,
        )