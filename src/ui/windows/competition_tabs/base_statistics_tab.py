from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics_service import StatisticsService
from src.services.data_quality_service import DataQualityService
from src.ui.dialogs.data_quality_dialog import DataQualityDialog
from src.ui.widgets.statistics_header_widget import (
    StatisticsHeaderWidget,
)


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class BaseStatisticsTab(QWidget):
    def __init__(
        self,
        title: str,
        refresh_button_text: str = "🔄 Aktualisieren",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.competition_id: int | None = None
        self.page_title = title
        self.content_widget: QWidget | None = None

        self.statistics_header = StatisticsHeaderWidget(
            title=title,
            subtitle="Kein Wettbewerb ausgewählt",
        )

        self.title_label = (
            self.statistics_header.title_label
        )
        self.info_label = (
            self.statistics_header.subtitle_label
        )

        self.refresh_button = QPushButton(
            refresh_button_text
        )

        self.main_layout = QVBoxLayout()
        self.header_row = QHBoxLayout()
        self.content_layout = QVBoxLayout()

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(
        self,
    ) -> None:
        self.setObjectName(
            "StatisticsTab"
        )

        self.main_layout.setContentsMargins(
            28,
            24,
            28,
            28,
        )

        self.main_layout.setSpacing(
            18
        )

        self.header_row.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.header_row.setSpacing(
            12
        )

        self.content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.content_layout.setSpacing(
            14
        )

        self.refresh_button.setObjectName(
            "StatisticsRefreshButton"
        )

        self.refresh_button.setMinimumHeight(
            36
        )

        self.refresh_button.setMaximumHeight(
            36
        )

        self.refresh_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        self.header_row.addWidget(
            self.statistics_header,
            1,
        )

        self.header_row.addWidget(
            self.refresh_button,
            0,
        )

        self.main_layout.addLayout(
            self.header_row
        )

        self.main_layout.addLayout(
            self.content_layout,
            stretch=1,
        )

        self.setLayout(
            self.main_layout
        )

    def connect_signals(
        self,
    ) -> None:
        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.statistics_header.quality_clicked_signal().connect(
            self.open_data_quality_dialog
        )

    def open_data_quality_dialog(
        self,
    ) -> None:
        if self.competition_id is None:
            return

        try:
            with self.database_connection() as connection:
                service = DataQualityService(
                    connection
                )
                quality = service.get_competition_quality(
                    self.competition_id
                )

            dialog = DataQualityDialog(
                quality=quality,
                parent=self,
            )
            dialog.exec()

        except Exception as error:
            self.show_error(
                message=(
                    "Die Datenqualität konnte "
                    "nicht geladen werden."
                ),
                error=error,
                title="Datenqualität",
            )

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()
        self._update_data_quality_header()

    def refresh(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.load_data()
        self._update_data_quality_header()

    def _update_data_quality_header(
        self,
    ) -> None:
        if self.competition_id is None:
            return

        try:
            with self.database_connection() as connection:
                service = DataQualityService(
                    connection
                )
                quality = service.get_competition_quality(
                    self.competition_id
                )

            self.statistics_header.set_source(
                quality.source_text
            )
            self.statistics_header.set_quality_percent(
                quality.overall_percent
            )
            self.statistics_header.set_data_status(
                quality.data_status_text
            )
            self.statistics_header.set_current_timestamp()

        except Exception as error:
            print(
                "[DATA QUALITY] "
                f"{self.page_title}: {error}"
            )
            self.statistics_header.set_source(
                "Unbekannt"
            )
            self.statistics_header.set_quality(
                "Nicht bewertet",
                StatisticsHeaderWidget.QUALITY_UNKNOWN,
            )
            self.statistics_header.set_data_status(
                "Datenstand nicht ermittelbar"
            )
            self.statistics_header.set_current_timestamp()

    def load_data(
        self,
    ) -> None:
        raise NotImplementedError(
            "load_data() muss in der Unterklasse "
            "implementiert werden."
        )

    def clear_data(
        self,
    ) -> None:
        self.set_info_text(
            "Kein Wettbewerb ausgewählt"
        )

        self.statistics_header.set_data_status(
            "Datenstand unbekannt"
        )

        self.statistics_header.set_quality(
            "Nicht bewertet",
            StatisticsHeaderWidget.QUALITY_UNKNOWN,
        )

        self.statistics_header.set_updated_at(
            None
        )

        self.refresh_button.setEnabled(
            False
        )

        self.clear_content()

    def clear_content(
        self,
    ) -> None:
        pass

    def add_content_widget(
        self,
        widget: QWidget,
        stretch: int = 0,
    ) -> None:
        self.content_widget = widget

        self.content_layout.addWidget(
            widget,
            stretch,
        )

    def add_content_layout(
        self,
        layout,
        stretch: int = 0,
    ) -> None:
        self.content_layout.addLayout(
            layout,
            stretch,
        )

    def set_info_text(
        self,
        text: str,
    ) -> None:
        self.statistics_header.set_subtitle(
            text
        )

    def set_refresh_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.refresh_button.setEnabled(
            enabled
        )

    def set_refresh_button_text(
        self,
        text: str,
    ) -> None:
        self.refresh_button.setText(
            text
        )

    def set_page_title(
        self,
        title: str,
    ) -> None:
        self.page_title = title

        self.statistics_header.set_title(
            title
        )

    def set_data_source(
        self,
        source: str,
    ) -> None:
        self.statistics_header.set_source(
            source
        )

    def set_data_quality(
        self,
        percent: float | None,
    ) -> None:
        self.statistics_header.set_quality_percent(
            percent
        )

    def set_data_status(
        self,
        text: str,
    ) -> None:
        self.statistics_header.set_data_status(
            text
        )

    def set_last_updated(
        self,
        value,
    ) -> None:
        self.statistics_header.set_updated_at(
            value
        )

    @contextmanager
    def database_connection(
        self,
    ) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            DATABASE_PATH
        )

        connection.row_factory = sqlite3.Row

        try:
            yield connection
        finally:
            connection.close()

    def get_competition_name(
        self,
        connection: sqlite3.Connection,
    ) -> str | None:
        if self.competition_id is None:
            return None

        statistics_service = StatisticsService(
            connection
        )

        return (
            statistics_service.get_competition_name(
                self.competition_id
            )
        )

    def show_error(
        self,
        message: str,
        error: Exception,
        title: str = "Fehler",
    ) -> None:
        QMessageBox.critical(
            self,
            title,
            f"{message}\n{error}",
        )

    def handle_load_error(
        self,
        message: str,
        error: Exception,
    ) -> None:
        self.show_error(
            message=message,
            error=error,
        )

        self.clear_data()
