from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class ClickableMetaLabel(QLabel):
    clicked = Signal()

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            text,
            parent,
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

    def mousePressEvent(
        self,
        event,
    ) -> None:
        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):
            self.clicked.emit()

        super().mousePressEvent(
            event
        )


class StatisticsHeaderWidget(QFrame):
    """
    Einheitlicher Informationskopf für Statistikseiten.

    Zeigt:
    - Titel
    - Untertitel
    - Datenquelle
    - Datenqualität
    - Datenstand
    - letzte Aktualisierung
    """

    QUALITY_GOOD = "good"
    QUALITY_MEDIUM = "medium"
    QUALITY_POOR = "poor"
    QUALITY_UNKNOWN = "unknown"

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = title.strip()
        self._subtitle = subtitle.strip()

        self._source_text = "FUSSBALL.DE"
        self._quality_text = "Nicht bewertet"
        self._quality_level = self.QUALITY_UNKNOWN
        self._data_status_text = "Datenstand unbekannt"
        self._updated_text = "Noch nicht aktualisiert"

        self.setObjectName(
            "StatisticsHeaderWidget"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        self.title_label = QLabel(
            self._title
        )
        self.subtitle_label = QLabel(
            self._subtitle
        )

        self.source_label = QLabel()
        self.quality_label = ClickableMetaLabel()
        self.data_status_label = QLabel()
        self.updated_label = QLabel()

        self._setup_ui()
        self._apply_style()
        self._refresh_metadata()

        self.quality_label.setToolTip(
            "Datenqualität im Detail anzeigen"
        )

    def _setup_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        root_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        text_layout = QVBoxLayout()

        text_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        text_layout.setSpacing(
            Metrics.SPACING_XXS
        )

        self.title_label.setObjectName(
            "StatisticsHeaderTitle"
        )

        self.title_label.setFont(
            Typography.heading()
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.subtitle_label.setObjectName(
            "StatisticsHeaderSubtitle"
        )

        self.subtitle_label.setFont(
            Typography.body()
        )

        self.subtitle_label.setWordWrap(
            True
        )

        self.subtitle_label.setVisible(
            bool(
                self._subtitle
            )
        )

        text_layout.addWidget(
            self.title_label
        )

        text_layout.addWidget(
            self.subtitle_label
        )

        root_layout.addLayout(
            text_layout
        )

        metadata_row = QHBoxLayout()

        metadata_row.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        metadata_row.setSpacing(
            Metrics.SPACING_SMALL
        )

        for label in (
            self.source_label,
            self.quality_label,
            self.data_status_label,
            self.updated_label,
        ):
            label.setAlignment(
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter
            )

            label.setSizePolicy(
                QSizePolicy.Policy.Maximum,
                QSizePolicy.Policy.Fixed,
            )

            label.setProperty(
                "statisticsMeta",
                True,
            )

            metadata_row.addWidget(
                label
            )

        metadata_row.addStretch(
            1
        )

        root_layout.addLayout(
            metadata_row
        )

    def _apply_style(
        self,
    ) -> None:
        self.setStyleSheet(
            f"""
            QFrame#StatisticsHeaderWidget {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_LARGE}px;
            }}

            QLabel#StatisticsHeaderTitle {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel#StatisticsHeaderSubtitle {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
                border:
                    none;
            }}

            QLabel[statisticsMeta="true"] {{
                color:
                    {Colors.TEXT_SECONDARY};
                background-color:
                    {Colors.BACKGROUND_ELEVATED};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
                padding:
                    4px 8px;
            }}

            QLabel[qualityLevel="good"] {{
                color:
                    {Colors.SUCCESS};
                border-color:
                    {Colors.SUCCESS};
                background-color:
                    {Colors.SUCCESS_SOFT};
            }}

            QLabel[qualityLevel="medium"] {{
                color:
                    {Colors.WARNING};
                border-color:
                    {Colors.WARNING};
                background-color:
                    {Colors.WARNING_SOFT};
            }}

            QLabel[qualityLevel="poor"] {{
                color:
                    {Colors.ERROR};
                border-color:
                    {Colors.ERROR};
                background-color:
                    {Colors.ERROR_SOFT};
            }}

            QLabel[qualityLevel="unknown"] {{
                color:
                    {Colors.TEXT_SECONDARY};
            }}
            """
        )

    def _refresh_metadata(
        self,
    ) -> None:
        self.source_label.setText(
            "Quelle: "
            f"{self._source_text}"
        )

        self.quality_label.setText(
            "Datenqualität: "
            f"{self._quality_text}"
        )

        self.data_status_label.setText(
            self._data_status_text
        )

        self.updated_label.setText(
            "Aktualisiert: "
            f"{self._updated_text}"
        )

        self.quality_label.setProperty(
            "qualityLevel",
            self._quality_level,
        )

        self.quality_label.style().unpolish(
            self.quality_label
        )

        self.quality_label.style().polish(
            self.quality_label
        )

        self.quality_label.update()

    def set_title(
        self,
        title: str,
    ) -> None:
        self._title = title.strip()

        self.title_label.setText(
            self._title
        )

    def set_subtitle(
        self,
        subtitle: str,
    ) -> None:
        self._subtitle = subtitle.strip()

        self.subtitle_label.setText(
            self._subtitle
        )

        self.subtitle_label.setVisible(
            bool(
                self._subtitle
            )
        )

    def set_source(
        self,
        source: str,
    ) -> None:
        source = source.strip()

        self._source_text = (
            source
            if source
            else "Unbekannt"
        )

        self._refresh_metadata()

    def set_quality(
        self,
        text: str,
        level: str = QUALITY_UNKNOWN,
    ) -> None:
        normalized_level = (
            level.strip().lower()
        )

        allowed_levels = {
            self.QUALITY_GOOD,
            self.QUALITY_MEDIUM,
            self.QUALITY_POOR,
            self.QUALITY_UNKNOWN,
        }

        if (
            normalized_level
            not in allowed_levels
        ):
            normalized_level = (
                self.QUALITY_UNKNOWN
            )

        normalized_text = text.strip()

        self._quality_text = (
            normalized_text
            if normalized_text
            else "Nicht bewertet"
        )

        self._quality_level = (
            normalized_level
        )

        self._refresh_metadata()

    def set_quality_percent(
        self,
        percent: float | None,
    ) -> None:
        if percent is None:
            self.set_quality(
                "Nicht bewertet",
                self.QUALITY_UNKNOWN,
            )
            return

        safe_percent = max(
            0.0,
            min(
                100.0,
                float(
                    percent
                ),
            ),
        )

        if safe_percent >= 90.0:
            level = self.QUALITY_GOOD
            label = "Gut"
        elif safe_percent >= 70.0:
            level = self.QUALITY_MEDIUM
            label = "Teilweise"
        else:
            level = self.QUALITY_POOR
            label = "Lückenhaft"

        self.set_quality(
            (
                f"{safe_percent:.0f} %"
                f" · {label}"
            ),
            level,
        )

    def set_data_status(
        self,
        text: str,
    ) -> None:
        text = text.strip()

        self._data_status_text = (
            text
            if text
            else "Datenstand unbekannt"
        )

        self._refresh_metadata()

    def set_updated_at(
        self,
        value: datetime | str | None,
    ) -> None:
        if isinstance(
            value,
            datetime,
        ):
            self._updated_text = (
                value.strftime(
                    "%d.%m.%Y · %H:%M"
                )
            )
        elif value:
            self._updated_text = str(
                value
            ).strip()
        else:
            self._updated_text = (
                "Unbekannt"
            )

        self._refresh_metadata()

    def set_current_timestamp(
        self,
    ) -> None:
        self.set_updated_at(
            datetime.now()
        )


    def quality_clicked_signal(
        self,
    ):
        return self.quality_label.clicked
