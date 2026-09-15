from __future__ import annotations

import queue
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.importer.fussballde.browser import FussballDeBrowser
from src.importer.fussballde.competition_browser import (
    CompetitionOption,
    FussballDeCompetitionBrowser,
)


@dataclass(frozen=True)
class BrowserCommand:
    action: str
    value: str | None = None


class CompetitionBrowserWorker(QThread):
    loaded = Signal(str, object)
    failed = Signal(str)
    ready = Signal()
    url_ready = Signal(str)
    stopped = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._commands: queue.Queue[BrowserCommand] = (
            queue.Queue()
        )
        self._stop_requested = False

        self.browser: FussballDeBrowser | None = None
        self.competition_browser: (
            FussballDeCompetitionBrowser | None
        ) = None

    def run(self) -> None:
        try:
            self._start_browser()

            while not self._stop_requested:
                try:
                    command = self._commands.get(
                        timeout=0.1
                    )
                except queue.Empty:
                    continue

                if command.action == "stop":
                    self._stop_requested = True
                    break

                try:
                    self._execute(
                        command
                    )
                except Exception as error:
                    self.failed.emit(
                        str(error)
                    )

        except Exception as error:
            self.failed.emit(
                str(error)
            )

        finally:
            self._close_browser()
            self.stopped.emit()

    def send(
        self,
        action: str,
        value: str | None = None,
    ) -> None:
        self._commands.put(
            BrowserCommand(
                action=action,
                value=value,
            )
        )

    def stop(self) -> None:
        self._stop_requested = True

        self._commands.put(
            BrowserCommand(
                action="stop"
            )
        )

    def _start_browser(self) -> None:
        self.browser = FussballDeBrowser()

        self.browser.start(
            headless=True,
        )

        self.competition_browser = (
            FussballDeCompetitionBrowser(
                self.browser
            )
        )

        self.competition_browser.open_selector()

        self.loaded.emit(
            "association",
            self.competition_browser.get_associations(),
        )

    def _execute(
        self,
        command: BrowserCommand,
    ) -> None:
        if self.competition_browser is None:
            raise RuntimeError(
                "FUSSBALL.DE-Browser ist nicht gestartet."
            )

        action = command.action
        value = command.value or ""

        if action == "association":
            self.competition_browser.select_association(
                value
            )
            self.loaded.emit(
                "season",
                self.competition_browser.get_seasons(),
            )

        elif action == "season":
            self.competition_browser.select_season(
                value
            )
            self.loaded.emit(
                "competition_type",
                self.competition_browser.get_competition_types(),
            )

        elif action == "competition_type":
            self.competition_browser.select_competition_type(
                value
            )
            self.loaded.emit(
                "team_type",
                self.competition_browser.get_team_types(),
            )

        elif action == "team_type":
            self.competition_browser.select_team_type(
                value
            )
            self.loaded.emit(
                "league",
                self.competition_browser.get_leagues(),
            )

        elif action == "league":
            self.competition_browser.select_league(
                value
            )
            self.loaded.emit(
                "area",
                self.competition_browser.get_areas(),
            )

        elif action == "area":
            self.competition_browser.select_area(
                value
            )
            self.loaded.emit(
                "competition",
                self.competition_browser.get_competitions(),
            )

        elif action == "competition":
            self.competition_browser.select_competition(
                value
            )
            self.ready.emit()

        elif action == "open":
            url = (
                self.competition_browser.open_competition()
            )
            self.url_ready.emit(
                url
            )

        else:
            raise RuntimeError(
                f"Unbekannte Browser-Aktion: {action}"
            )

    def _close_browser(self) -> None:
        try:
            if (
                self.browser is not None
                and self.browser.browser is not None
            ):
                self.browser.browser.close()
        except Exception:
            pass

        try:
            if (
                self.browser is not None
                and self.browser.playwright is not None
            ):
                self.browser.playwright.stop()
        except Exception:
            pass


class FussballDeCompetitionDialog(QDialog):
    """
    Dialog zur Auswahl einer FUSSBALL.DE-Staffel.

    Playwright läuft während der gesamten Dialog-Laufzeit
    in genau einem dauerhaft aktiven Worker-Thread.
    """

    FIELD_ORDER = (
        "association",
        "season",
        "competition_type",
        "team_type",
        "league",
        "area",
        "competition",
    )

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "FUSSBALL.DE - Staffel auswählen"
        )
        self.resize(
            620,
            430,
        )

        self.selected_url: str | None = None
        self._closing = False

        self.worker = CompetitionBrowserWorker()

        self.worker.loaded.connect(
            self._on_loaded
        )
        self.worker.failed.connect(
            self._on_failed
        )
        self.worker.ready.connect(
            self._on_ready
        )
        self.worker.url_ready.connect(
            self._on_url_ready
        )

        self._build_ui()
        self._connect_signals()
        self._set_initial_state()

        self.status_label.setText(
            "FUSSBALL.DE wird geladen..."
        )

        self.worker.start()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(
            self
        )

        title = QLabel(
            "Staffel auf FUSSBALL.DE auswählen"
        )
        title.setObjectName(
            "DialogTitle"
        )

        description = QLabel(
            "Die Auswahl wird direkt von FUSSBALL.DE geladen. "
            "Nach jeder Auswahl wird die nächste Ebene automatisch "
            "freigeschaltet."
        )
        description.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )
        layout.addWidget(
            description
        )

        form = QFormLayout()

        self.association_combo = QComboBox()
        self.season_combo = QComboBox()
        self.competition_type_combo = QComboBox()
        self.team_type_combo = QComboBox()
        self.league_combo = QComboBox()
        self.area_combo = QComboBox()
        self.competition_combo = QComboBox()

        form.addRow(
            "Verband:",
            self.association_combo,
        )
        form.addRow(
            "Saison:",
            self.season_combo,
        )
        form.addRow(
            "Typ:",
            self.competition_type_combo,
        )
        form.addRow(
            "Mannschaftsart:",
            self.team_type_combo,
        )
        form.addRow(
            "Spielklasse:",
            self.league_combo,
        )
        form.addRow(
            "Gebiet / Kreis:",
            self.area_combo,
        )
        form.addRow(
            "Staffel:",
            self.competition_combo,
        )

        layout.addLayout(
            form
        )

        self.status_label = QLabel()
        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.status_label
        )

        self.button_box = QDialogButtonBox()

        self.accept_button = QPushButton(
            "Staffel übernehmen"
        )
        self.cancel_button = QPushButton(
            "Abbrechen"
        )

        self.button_box.addButton(
            self.accept_button,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.button_box.addButton(
            self.cancel_button,
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        layout.addWidget(
            self.button_box
        )

    def _connect_signals(self) -> None:
        self.association_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "association",
                index,
            )
        )

        self.season_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "season",
                index,
            )
        )

        self.competition_type_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "competition_type",
                index,
            )
        )

        self.team_type_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "team_type",
                index,
            )
        )

        self.league_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "league",
                index,
            )
        )

        self.area_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "area",
                index,
            )
        )

        self.competition_combo.currentIndexChanged.connect(
            lambda index: self._selection_changed(
                "competition",
                index,
            )
        )

        self.accept_button.clicked.connect(
            self._accept_selection
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

    def _set_initial_state(self) -> None:
        for combo in self._all_combos():
            combo.clear()
            combo.addItem(
                "Wird geladen..."
            )
            combo.setEnabled(
                False
            )

        self.accept_button.setEnabled(
            False
        )

    def _selection_changed(
        self,
        field: str,
        index: int,
    ) -> None:
        combo = self._combo_for_field(
            field
        )

        if index <= 0:
            self._reset_after(
                field
            )
            return

        option = combo.currentData()

        if not isinstance(
            option,
            CompetitionOption,
        ):
            return

        self._reset_after(
            field
        )
        self._set_busy(
            True
        )

        self.status_label.setText(
            f"Lade Auswahl nach '{option.label}'..."
        )

        self.worker.send(
            field,
            option.label,
        )

    def _on_loaded(
        self,
        field: str,
        options: object,
    ) -> None:
        if not isinstance(
            options,
            list,
        ):
            options = []

        combo = self._combo_for_field(
            field
        )

        combo.blockSignals(
            True
        )
        combo.clear()
        combo.addItem(
            self._placeholder_for_field(
                field
            )
        )

        for option in options:
            if isinstance(
                option,
                CompetitionOption,
            ):
                combo.addItem(
                    option.label,
                    option,
                )

        combo.setCurrentIndex(
            0
        )
        combo.setEnabled(
            combo.count() > 1
        )
        combo.blockSignals(
            False
        )

        self._set_busy(
            False
        )

        if field == "association":
            self.status_label.setText(
                "Verband auswählen."
            )
        else:
            self.status_label.setText(
                "Nächste Auswahl treffen."
            )

        self._select_default_if_available(
            field
        )

    def _on_ready(self) -> None:
        self._set_busy(
            False
        )

        self.accept_button.setEnabled(
            True
        )

        self.status_label.setText(
            "Staffel vollständig ausgewählt."
        )

    def _on_url_ready(
        self,
        url: str,
    ) -> None:
        self.selected_url = url
        self.accept()

    def _on_failed(
        self,
        message: str,
    ) -> None:
        self._set_busy(
            False
        )

        self.status_label.setText(
            "FUSSBALL.DE konnte nicht geladen werden."
        )

        QMessageBox.critical(
            self,
            "FUSSBALL.DE",
            message,
        )

    def _accept_selection(self) -> None:
        if not self.accept_button.isEnabled():
            return

        self._set_busy(
            True
        )

        self.status_label.setText(
            "Staffel-URL wird ermittelt..."
        )

        self.worker.send(
            "open"
        )

    def get_selected_url(
        self,
    ) -> str | None:
        return self.selected_url

    def _reset_after(
        self,
        field: str,
    ) -> None:
        try:
            index = self.FIELD_ORDER.index(
                field
            )
        except ValueError:
            return

        for later_field in self.FIELD_ORDER[
            index + 1:
        ]:
            combo = self._combo_for_field(
                later_field
            )

            combo.blockSignals(
                True
            )
            combo.clear()
            combo.addItem(
                self._placeholder_for_field(
                    later_field
                )
            )
            combo.setEnabled(
                False
            )
            combo.blockSignals(
                False
            )

        self.accept_button.setEnabled(
            False
        )

    def _set_busy(
        self,
        busy: bool,
    ) -> None:
        if busy:
            for combo in self._all_combos():
                combo.setEnabled(
                    False
                )

            self.accept_button.setEnabled(
                False
            )
            return

        for combo in self._all_combos():
            if combo.count() > 1:
                combo.setEnabled(
                    True
                )

    def _select_default_if_available(
        self,
        field: str,
    ) -> None:
        defaults = {
            "association": "Rheinland",
            "competition_type": "Meisterschaften",
            "team_type": "Herren",
        }

        default = defaults.get(
            field
        )

        if default is None:
            return

        combo = self._combo_for_field(
            field
        )

        index = combo.findText(
            default
        )

        if index > 0:
            combo.setCurrentIndex(
                index
            )

    def _combo_for_field(
        self,
        field: str,
    ) -> QComboBox:
        mapping = {
            "association": self.association_combo,
            "season": self.season_combo,
            "competition_type": self.competition_type_combo,
            "team_type": self.team_type_combo,
            "league": self.league_combo,
            "area": self.area_combo,
            "competition": self.competition_combo,
        }

        try:
            return mapping[field]
        except KeyError as error:
            raise ValueError(
                f"Unbekanntes Feld: {field}"
            ) from error

    def _all_combos(
        self,
    ) -> tuple[QComboBox, ...]:
        return (
            self.association_combo,
            self.season_combo,
            self.competition_type_combo,
            self.team_type_combo,
            self.league_combo,
            self.area_combo,
            self.competition_combo,
        )

    @staticmethod
    def _placeholder_for_field(
        field: str,
    ) -> str:
        placeholders = {
            "association": "Verband auswählen",
            "season": "Saison auswählen",
            "competition_type": "Typ auswählen",
            "team_type": "Mannschaftsart auswählen",
            "league": "Spielklasse auswählen",
            "area": "Gebiet / Kreis auswählen",
            "competition": "Staffel auswählen",
        }

        return placeholders.get(
            field,
            "Auswählen",
        )

    def done(
        self,
        result: int,
    ) -> None:
        if self._closing:
            return

        self._closing = True

        if self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(
                5_000
            )

        super().done(
            result
        )

    def closeEvent(
        self,
        event,
    ) -> None:
        if not self._closing:
            self._closing = True

            if self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(
                    5_000
                )

        super().closeEvent(
            event
        )
