import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics_service import StatisticsService


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

        self.title_label = QLabel(title)

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button = QPushButton(
            refresh_button_text
        )

        self.header_frame = QFrame()
        self.header_frame.setObjectName(
            "StatisticsHeaderFrame"
        )

        self.main_layout = QVBoxLayout()
        self.header_frame_layout = QVBoxLayout()
        self.header_layout = QHBoxLayout()
        self.content_layout = QVBoxLayout()

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self) -> None:
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

        self.header_frame_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        self.header_frame_layout.setSpacing(
            8
        )

        self.header_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.header_layout.setSpacing(
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

        self.title_label.setObjectName(
            "PageTitle"
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignLeft
        )

        self.info_label.setObjectName(
            "InfoLabel"
        )

        self.info_label.setWordWrap(
            True
        )

        self.info_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignLeft
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

        self.header_layout.addWidget(
            self.title_label
        )

        self.header_layout.addStretch()

        self.header_layout.addWidget(
            self.refresh_button
        )

        self.header_frame_layout.addLayout(
            self.header_layout
        )

        self.header_frame_layout.addWidget(
            self.info_label
        )

        self.header_frame.setLayout(
            self.header_frame_layout
        )

        self.main_layout.addWidget(
            self.header_frame
        )

        self.main_layout.addLayout(
            self.content_layout,
            stretch=1,
        )

        self.setLayout(
            self.main_layout
        )

    def connect_signals(self) -> None:
        self.refresh_button.clicked.connect(
            self.refresh
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

    def refresh(self) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(self) -> None:
        raise NotImplementedError(
            "load_data() muss in der Unterklasse "
            "implementiert werden."
        )

    def clear_data(self) -> None:
        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(
            False
        )

        self.clear_content()

    def clear_content(self) -> None:
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
        self.info_label.setText(
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
        self.title_label.setText(
            title
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