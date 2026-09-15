from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import (
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from src.importer.fussballde.browser import FussballDeBrowser


@dataclass(frozen=True)
class CompetitionOption:
    label: str
    value: str


class FussballDeCompetitionBrowser:
    """
    Steuert die dynamische Wettbewerbsauswahl auf FUSSBALL.DE.

    Auswahlkette:
        Verband
        -> Saison
        -> Typ
        -> Mannschaftsart
        -> Spielklasse
        -> Gebiet
        -> Wettbewerb / Staffel
    """

    START_URL = "https://www.fussball.de/"

    FIELD_ASSOCIATION = "clients"
    FIELD_SEASON = "seasons"
    FIELD_COMPETITION_TYPE = "competitionTypes"
    FIELD_TEAM_TYPE = "teamTypes"
    FIELD_LEAGUE = "leagues"
    FIELD_AREA = "areas"
    FIELD_COMPETITION = "competitions"

    FIELD_ORDER = (
        FIELD_ASSOCIATION,
        FIELD_SEASON,
        FIELD_COMPETITION_TYPE,
        FIELD_TEAM_TYPE,
        FIELD_LEAGUE,
        FIELD_AREA,
        FIELD_COMPETITION,
    )

    DEFAULT_TIMEOUT = 15_000

    def __init__(
        self,
        browser: FussballDeBrowser,
    ) -> None:
        self.browser = browser

    @property
    def page(self) -> Page:
        if self.browser.page is None:
            raise RuntimeError(
                "Browser wurde noch nicht gestartet."
            )

        return self.browser.page

    def open_selector(self) -> None:
        self.browser.open(
            self.START_URL,
            page_type=FussballDeBrowser.PAGE_TYPE_GENERIC,
        )

        self._wait_for_field(
            self.FIELD_ASSOCIATION,
        )

    # ------------------------------------------------------------------
    # Optionen lesen
    # ------------------------------------------------------------------

    def get_associations(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_ASSOCIATION,
        )

    def get_seasons(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_SEASON,
        )

    def get_competition_types(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_COMPETITION_TYPE,
        )

    def get_team_types(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_TEAM_TYPE,
        )

    def get_leagues(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_LEAGUE,
        )

    def get_areas(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_AREA,
        )

    def get_competitions(
        self,
    ) -> list[CompetitionOption]:
        return self._get_options(
            self.FIELD_COMPETITION,
        )

    # ------------------------------------------------------------------
    # Auswahl setzen
    # ------------------------------------------------------------------

    def select_association(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_ASSOCIATION,
            label,
        )

    def select_season(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_SEASON,
            label,
        )

    def select_competition_type(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_COMPETITION_TYPE,
            label,
        )

    def select_team_type(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_TEAM_TYPE,
            label,
        )

    def select_league(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_LEAGUE,
            label,
        )

    def select_area(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_AREA,
            label,
        )

    def select_competition(
        self,
        label: str,
    ) -> None:
        self._select(
            self.FIELD_COMPETITION,
            label,
        )

    # ------------------------------------------------------------------
    # Status / Navigation
    # ------------------------------------------------------------------

    def get_selected_values(
        self,
    ) -> dict[str, CompetitionOption | None]:
        result: dict[
            str,
            CompetitionOption | None,
        ] = {}

        for field_name in self.FIELD_ORDER:
            locator = self._field(
                field_name,
            )

            try:
                selected = locator.locator(
                    "option:checked"
                ).first

                if selected.count() == 0:
                    result[field_name] = None
                    continue

                label = selected.inner_text().strip()
                value = selected.get_attribute(
                    "value"
                ) or ""

                if self._is_placeholder(
                    label=label,
                    value=value,
                ):
                    result[field_name] = None
                    continue

                result[field_name] = (
                    CompetitionOption(
                        label=label,
                        value=value,
                    )
                )

            except Exception:
                result[field_name] = None

        return result

    def is_ready_to_open(
        self,
    ) -> bool:
        competition = self._field(
            self.FIELD_COMPETITION,
        )

        if competition.is_disabled():
            return False

        selected = competition.locator(
            "option:checked"
        ).first

        if selected.count() == 0:
            return False

        label = selected.inner_text().strip()
        value = selected.get_attribute(
            "value"
        ) or ""

        return not self._is_placeholder(
            label=label,
            value=value,
        )

    def open_competition(
        self,
    ) -> str:
        if not self.is_ready_to_open():
            raise RuntimeError(
                "Es wurde noch keine vollständige "
                "Staffel ausgewählt."
            )

        button = self._find_show_button()

        old_url = self.page.url

        try:
            button.click(
                timeout=self.DEFAULT_TIMEOUT,
            )
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                "Der FUSSBALL.DE-Button 'Anzeigen' "
                "konnte nicht ausgelöst werden."
            ) from error

        try:
            self.page.wait_for_url(
                lambda url: url != old_url,
                timeout=self.DEFAULT_TIMEOUT,
            )
        except PlaywrightTimeoutError:
            try:
                self.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=5_000,
                )
            except PlaywrightTimeoutError:
                pass

        self.page.wait_for_timeout(1_000)

        result_url = self.page.url

        if result_url == old_url:
            raise RuntimeError(
                "FUSSBALL.DE hat nach 'Anzeigen' "
                "keine neue Wettbewerbsseite geöffnet."
            )

        return result_url

    # ------------------------------------------------------------------
    # Interne Hilfsmethoden
    # ------------------------------------------------------------------

    def _get_options(
        self,
        field_name: str,
    ) -> list[CompetitionOption]:
        locator = self._field(
            field_name,
        )

        options = locator.locator(
            "option"
        )

        result: list[CompetitionOption] = []

        for index in range(
            options.count()
        ):
            option = options.nth(index)

            label = option.inner_text().strip()
            value = option.get_attribute(
                "value"
            ) or ""

            if self._is_placeholder(
                label=label,
                value=value,
            ):
                continue

            result.append(
                CompetitionOption(
                    label=label,
                    value=value,
                )
            )

        return result

    def _select(
        self,
        field_name: str,
        label: str,
    ) -> None:
        label = label.strip()

        if not label:
            raise ValueError(
                "Auswahl darf nicht leer sein."
            )

        locator = self._field(
            field_name,
        )

        if locator.is_disabled():
            raise RuntimeError(
                f"Das Feld '{field_name}' ist "
                "noch nicht freigeschaltet."
            )

        available_labels = {
            option.label
            for option in self._get_options(
                field_name,
            )
        }

        if label not in available_labels:
            raise ValueError(
                f"'{label}' ist für "
                f"'{field_name}' nicht verfügbar."
            )

        next_field = self._next_field(
            field_name,
        )

        previous_state = None

        if next_field is not None:
            previous_state = (
                self._field_state(
                    next_field,
                )
            )

        changed = locator.evaluate(
            """
            (element, expectedLabel) => {
                const options =
                    Array.from(element.options);

                const option =
                    options.find(
                        item =>
                            item.textContent.trim()
                            === expectedLabel
                    );

                if (!option) {
                    return false;
                }

                element.value = option.value;

                option.selected = true;

                element.dispatchEvent(
                    new Event(
                        "change",
                        {
                            bubbles: true
                        }
                    )
                );

                return true;
            }
            """,
            label,
        )

        if not changed:
            raise RuntimeError(
                f"Auswahl '{label}' in "
                f"'{field_name}' konnte nicht "
                "gesetzt werden."
            )

        self.page.wait_for_timeout(250)

        self._wait_until_selected(
            field_name=field_name,
            label=label,
        )

        if next_field is not None:
            self._wait_for_dynamic_update(
                field_name=next_field,
                previous_state=previous_state,
            )

    def _field(
        self,
        field_name: str,
    ) -> Locator:
        candidates = self.page.locator(
            f"select[name='{field_name}']"
        )

        if candidates.count() == 0:
            raise RuntimeError(
                f"FUSSBALL.DE-Feld "
                f"'{field_name}' wurde nicht gefunden."
            )

        # FUSSBALL.DE rendert dieselbe Wettbewerbsauswahl
        # teilweise mehrfach. Die nativen <select>-Elemente können
        # dabei durch das WAM-Widget selbst unsichtbar sein.
        #
        # Deshalb bevorzugen wir:
        # 1. sichtbare native Selects,
        # 2. ansonsten ein Select aus einem sichtbaren Elternbereich,
        # 3. zuletzt das letzte passende Select statt blind .first.

        for index in range(
            candidates.count()
        ):
            candidate = candidates.nth(
                index
            )

            try:
                if candidate.is_visible():
                    return candidate
            except Exception:
                continue

        for index in range(
            candidates.count()
        ):
            candidate = candidates.nth(
                index
            )

            try:
                in_visible_area = candidate.evaluate(
                    """
                    element => {
                        let parent = element.parentElement;

                        while (parent) {
                            const style =
                                window.getComputedStyle(parent);

                            const rect =
                                parent.getBoundingClientRect();

                            if (
                                style.display === "none"
                                || style.visibility === "hidden"
                            ) {
                                return false;
                            }

                            if (
                                rect.width > 0
                                && rect.height > 0
                            ) {
                                return true;
                            }

                            parent = parent.parentElement;
                        }

                        return false;
                    }
                    """
                )

                if in_visible_area:
                    return candidate

            except Exception:
                continue

        return candidates.last

    def _wait_for_field(
        self,
        field_name: str,
    ) -> None:
        try:
            self.page.locator(
                f"select[name='{field_name}']"
            ).first.wait_for(
                state="attached",
                timeout=self.DEFAULT_TIMEOUT,
            )
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                f"FUSSBALL.DE-Feld "
                f"'{field_name}' wurde nicht geladen."
            ) from error

    def _wait_until_selected(
        self,
        field_name: str,
        label: str,
    ) -> None:
        locator = self._field(
            field_name,
        )

        try:
            self.page.wait_for_function(
                """
                ([element, expectedLabel]) => {
                    const option =
                        element.options[
                            element.selectedIndex
                        ];

                    return (
                        option
                        && option.textContent.trim()
                            === expectedLabel
                    );
                }
                """,
                arg=[
                    locator.element_handle(),
                    label,
                ],
                timeout=self.DEFAULT_TIMEOUT,
            )
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                f"Auswahl '{label}' in "
                f"'{field_name}' wurde nicht übernommen."
            ) from error

    def _wait_for_dynamic_update(
        self,
        field_name: str,
        previous_state: tuple[
            bool,
            tuple[tuple[str, str], ...],
        ] | None,
    ) -> None:
        deadline = (
            self.page.evaluate(
                "() => Date.now()"
            )
            + self.DEFAULT_TIMEOUT
        )

        while True:
            current_state = self._field_state(
                field_name,
            )

            if (
                previous_state is None
                or current_state != previous_state
            ):
                self.page.wait_for_timeout(
                    250
                )
                return

            now = self.page.evaluate(
                "() => Date.now()"
            )

            if now >= deadline:
                # Nicht jede Auswahl verändert zwingend
                # sofort das direkt folgende Feld.
                # Deshalb hier kein harter Fehler.
                return

            self.page.wait_for_timeout(
                100
            )

    def _field_state(
        self,
        field_name: str,
    ) -> tuple[
        bool,
        tuple[tuple[str, str], ...],
    ]:
        locator = self._field(
            field_name,
        )

        disabled = locator.is_disabled()

        options: list[
            tuple[str, str]
        ] = []

        option_locators = locator.locator(
            "option"
        )

        for index in range(
            option_locators.count()
        ):
            option = option_locators.nth(
                index
            )

            options.append(
                (
                    option.inner_text().strip(),
                    option.get_attribute(
                        "value"
                    ) or "",
                )
            )

        return (
            disabled,
            tuple(options),
        )

    def _next_field(
        self,
        field_name: str,
    ) -> str | None:
        try:
            index = self.FIELD_ORDER.index(
                field_name
            )
        except ValueError:
            return None

        next_index = index + 1

        if next_index >= len(
            self.FIELD_ORDER
        ):
            return None

        return self.FIELD_ORDER[
            next_index
        ]

    def _find_show_button(
        self,
    ) -> Locator:
        buttons = self.page.locator(
            "button[type='submit']"
        )

        for index in range(
            buttons.count()
        ):
            button = buttons.nth(
                index
            )

            try:
                if not button.is_visible():
                    continue

                text = button.inner_text().strip()

                if (
                    text.casefold()
                    != "anzeigen"
                ):
                    continue

                if button.is_disabled():
                    continue

                return button

            except Exception:
                continue

        raise RuntimeError(
            "Der aktive FUSSBALL.DE-Button "
            "'Anzeigen' wurde nicht gefunden."
        )

    @staticmethod
    def _is_placeholder(
        label: str,
        value: str,
    ) -> bool:
        normalized_label = (
            label.casefold().strip()
        )
        normalized_value = (
            value.casefold().strip()
        )

        if normalized_value in {
            "",
            "null",
            "-1",
        }:
            return True

        placeholder_words = (
            " wählen",
            "auswählen",
        )

        return any(
            word in normalized_label
            for word in placeholder_words
        )


def _print_options(
    title: str,
    options: list[CompetitionOption],
) -> None:
    print()
    print(title)
    print("-" * 60)

    if not options:
        print("Keine Optionen verfügbar.")
        return

    for option in options:
        print(
            f"{option.label:<45} "
            f"{option.value}"
        )


def main() -> None:
    browser = FussballDeBrowser()

    try:
        print("Starte Chromium...")

        browser.start(
            headless=False,
        )

        competition_browser = (
            FussballDeCompetitionBrowser(
                browser
            )
        )

        print("Öffne FUSSBALL.DE...")
        competition_browser.open_selector()

        print()
        print("=" * 70)
        print("FUSSBALL.DE STAFFEL-TEST")
        print("=" * 70)

        print("[1/7] Verband: Rheinland")
        competition_browser.select_association(
            "Rheinland"
        )

        print("[2/7] Saison: 26/27")
        competition_browser.select_season(
            "26/27"
        )

        print("[3/7] Typ: Meisterschaften")
        competition_browser.select_competition_type(
            "Meisterschaften"
        )

        print("[4/7] Mannschaftsart: Herren")
        competition_browser.select_team_type(
            "Herren"
        )

        print("[5/7] Spielklasse: Reserveklasse")
        competition_browser.select_league(
            "Reserveklasse"
        )

        areas = competition_browser.get_areas()

        _print_options(
            "VERFÜGBARE GEBIETE / KREISE:",
            areas,
        )

        target_area = "Kreis Trier/Saarburg"

        area_labels = {
            option.label
            for option in areas
        }

        if target_area not in area_labels:
            print()
            print(
                f"HINWEIS: '{target_area}' wurde "
                "nicht exakt gefunden."
            )
            print(
                "Der Test endet hier, damit wir "
                "keinen falschen Kreis auswählen."
            )
            return

        print()
        print(
            f"[6/7] Gebiet: {target_area}"
        )

        competition_browser.select_area(
            target_area
        )

        competitions = (
            competition_browser
            .get_competitions()
        )

        _print_options(
            "VERFÜGBARE WETTBEWERBE / STAFFELN:",
            competitions,
        )

        target_competition = (
            "Reserveklasse Trier-Saarburg"
        )

        competition_labels = {
            option.label
            for option in competitions
        }

        if (
            target_competition
            not in competition_labels
        ):
            print()
            print(
                f"HINWEIS: '{target_competition}' "
                "wurde nicht exakt gefunden."
            )
            print(
                "Der Test endet hier, damit wir "
                "keine falsche Staffel öffnen."
            )
            return

        print()
        print(
            f"[7/7] Staffel: "
            f"{target_competition}"
        )

        competition_browser.select_competition(
            target_competition
        )

        print()
        print("Aktuelle Auswahl:")
        print("-" * 60)

        selected = (
            competition_browser
            .get_selected_values()
        )

        for field_name in (
            competition_browser.FIELD_ORDER
        ):
            option = selected.get(
                field_name
            )

            if option is None:
                print(
                    f"{field_name:<20} -"
                )
            else:
                print(
                    f"{field_name:<20} "
                    f"{option.label} "
                    f"({option.value})"
                )

        print()
        print(
            "Bereit zum Öffnen:",
            competition_browser
            .is_ready_to_open(),
        )

        print()
        print(
            "Klicke ANZEIGEN und ermittle "
            "die Staffel-URL..."
        )

        staffel_url = (
            competition_browser
            .open_competition()
        )

        print()
        print("=" * 70)
        print("STAFFEL ERFOLGREICH GEÖFFNET")
        print("=" * 70)
        print(staffel_url)
        print("=" * 70)

        print()
        print(
            "Browser bleibt 5 Sekunden offen..."
        )
        competition_browser.page.wait_for_timeout(
            5_000
        )

    finally:
        if browser.browser is not None:
            browser.browser.close()

        if browser.playwright is not None:
            browser.playwright.stop()


if __name__ == "__main__":
    main()
