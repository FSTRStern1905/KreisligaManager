from __future__ import annotations

import re
import sqlite3
from datetime import datetime
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

            self._prepare_full_schedule_range(
                browser.page
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

            finished_matches = [
                schedule_match
                for schedule_match in schedule_matches
                if self._is_finished_match(
                    schedule_match
                )
            ]

            detail_matches = finished_matches

            if max_detail_matches is not None:
                detail_matches = (
                    finished_matches[
                        :max_detail_matches
                    ]
                )

            skipped_detail_matches = (
                len(schedule_matches)
                - len(finished_matches)
            )

            print(
                "Abgeschlossene Spiele mit "
                "Detailimport: "
                f"{len(detail_matches)} von "
                f"{len(finished_matches)}"
            )

            print(
                "Nicht abgeschlossene / noch nicht "
                "terminierte Spiele nur im Spielplan: "
                f"{skipped_detail_matches}"
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

    @classmethod
    def _prepare_full_schedule_range(
        cls,
        page: Any,
    ) -> None:
        """
        Lädt für laufende Wettbewerbe den vollständigen
        Staffelspielplan.

        Wichtig:
        FUSSBALL.DE besitzt mehrere Datumsfilter auf derselben Seite.
        Für den Staffelspielplan sind ausschließlich diese Felder
        relevant:

            #matchtable-date-from
            #matchtable-date-to

        Außerdem wird nur der Submit-Button des Formulars mit
        data-ajax-resource*="ajax.fixturelist" verwendet.
        """
        from_input = page.locator(
            "#matchtable-date-from"
        )
        to_input = page.locator(
            "#matchtable-date-to"
        )

        if (
            from_input.count() < 1
            or to_input.count() < 1
        ):
            print(
                "Spielplan-Zeitraum: Staffel-Datumsfelder "
                "nicht gefunden. Aktueller Zeitraum bleibt aktiv."
            )
            return

        current_from = (
            from_input.first.input_value()
            .strip()
        )
        current_to = (
            to_input.first.input_value()
            .strip()
        )

        target_from = cls._derive_season_start_date(
            page=page,
            current_to=current_to,
        )

        if not target_from:
            print(
                "Spielplan-Zeitraum: Saisonbeginn konnte "
                "nicht bestimmt werden."
            )
            return

        try:
            current_from_date = datetime.strptime(
                current_from,
                "%d.%m.%Y",
            ).date()

            target_from_date = datetime.strptime(
                target_from,
                "%d.%m.%Y",
            ).date()
        except ValueError:
            current_from_date = None
            target_from_date = None

        if (
            current_from_date is not None
            and target_from_date is not None
            and current_from_date <= target_from_date
        ):
            print(
                "Spielplan-Zeitraum bereits vollständig: "
                f"{current_from} bis {current_to}"
            )
            return

        print(
            "Spielplan-Zeitraum erweitern: "
            f"{current_from} -> {target_from}"
        )

        cls._set_date_input_value(
            page=page,
            selector="#matchtable-date-from",
            value=target_from,
        )

        cls._set_date_input_value(
            page=page,
            selector="#matchtable-date-to",
            value=current_to,
        )

        fixture_form = page.locator(
            "form[data-ajax-resource*='ajax.fixturelist']"
        )

        if fixture_form.count() < 1:
            print(
                "WARNUNG: Staffelspielplan-Formular wurde "
                "nicht gefunden. Import läuft mit aktuellem "
                "Zeitraum weiter."
            )
            return

        submit_button = fixture_form.first.locator(
            "button[type='submit']"
        )

        if submit_button.count() < 1:
            print(
                "WARNUNG: Submit-Button des Staffelspielplans "
                "wurde nicht gefunden. Import läuft mit aktuellem "
                "Zeitraum weiter."
            )
            return

        try:
            with page.expect_response(
                lambda response: (
                    "ajax.fixturelist"
                    in response.url
                ),
                timeout=10000,
            ):
                submit_button.first.click(
                    force=True
                )
        except Exception:
            # Fallback: Klick ausführen und anschließend kurz auf
            # die AJAX-Aktualisierung warten.
            try:
                submit_button.first.click(
                    force=True
                )
            except Exception as error:
                print(
                    "WARNUNG: Staffelspielplan konnte nicht "
                    "neu geladen werden: "
                    f"{error}"
                )
                return

        page.wait_for_timeout(
            1800
        )

        try:
            new_from = (
                page.locator(
                    "#matchtable-date-from"
                )
                .first
                .input_value()
                .strip()
            )
        except Exception:
            new_from = target_from

        print(
            "Spielplan-Zeitraum geladen: "
            f"{new_from} bis {current_to}"
        )

    @classmethod
    def _derive_season_start_date(
        cls,
        page: Any,
        current_to: str,
    ) -> str:
        """
        Ermittelt einen sicheren Saisonbeginn.

        Wenn die URL z. B. 'saison2627' enthält, wird daraus
        01.07.2026. Damit werden auch frühe Spieltage sicher
        mitgeladen, ohne den exakten 1. Spieltag kennen zu müssen.
        """
        page_url = str(
            getattr(
                page,
                "url",
                "",
            )
            or ""
        )

        season_match = re.search(
            r"saison(\d{2})(\d{2})",
            page_url,
            re.IGNORECASE,
        )

        if season_match:
            start_year_short = int(
                season_match.group(1)
            )

            start_year = (
                2000
                + start_year_short
            )

            return (
                f"01.07.{start_year}"
            )

        try:
            end_year = datetime.strptime(
                current_to,
                "%d.%m.%Y",
            ).year

            return (
                f"01.07.{end_year - 1}"
            )
        except ValueError:
            return ""

    @staticmethod
    def _set_date_input_value(
        page: Any,
        selector: str,
        value: str,
    ) -> None:
        """
        Setzt ein readonly AngularJS-Datumsfeld so, dass sowohl
        das DOM als auch Angulars ngModel die Änderung erhalten.
        """
        locator = page.locator(
            selector
        ).first

        locator.evaluate(
            """(element, value) => {
                element.removeAttribute('readonly');
                element.value = value;

                element.dispatchEvent(
                    new Event(
                        'input',
                        { bubbles: true }
                    )
                );

                element.dispatchEvent(
                    new Event(
                        'change',
                        { bubbles: true }
                    )
                );

                element.dispatchEvent(
                    new Event(
                        'blur',
                        { bubbles: true }
                    )
                );
            }""",
            value,
        )

        # AngularJS direkt synchronisieren, falls auf der Seite
        # verfügbar. So serialisiert data-rest-form garantiert den
        # neuen Wert.
        page.evaluate(
            """([selector, value]) => {
                if (!window.angular) {
                    return;
                }

                const element = document.querySelector(
                    selector
                );

                if (!element) {
                    return;
                }

                const ngElement = window.angular.element(
                    element
                );

                const controller = ngElement.controller(
                    'ngModel'
                );

                if (!controller) {
                    return;
                }

                controller.$setViewValue(
                    value
                );

                controller.$render();

                const scope = ngElement.scope();

                if (
                    scope
                    && !scope.$root.$$phase
                ) {
                    scope.$apply();
                }
            }""",
            [
                selector,
                value,
            ],
        )

    @classmethod
    def _is_finished_match(
        cls,
        schedule_match: Any,
    ) -> bool:
        status = str(
            cls._get_value(
                schedule_match,
                "status",
                "",
            )
            or ""
        ).strip().casefold()

        home_score = cls._get_value(
            schedule_match,
            "home_score",
            None,
        )

        away_score = cls._get_value(
            schedule_match,
            "away_score",
            None,
        )

        if status == "finished":
            return True

        return (
            home_score is not None
            and away_score is not None
        )

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