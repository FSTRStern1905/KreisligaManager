from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.data_quality_service import (
    CompetitionDataQuality,
    DataQualityMetric,
)
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class DataQualityDialog(QDialog):
    def __init__(
        self,
        quality: CompetitionDataQuality,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self.quality = quality

        self.setObjectName(
            "DataQualityDialog"
        )

        self.setWindowTitle(
            "Datenqualität"
        )

        self.setMinimumSize(
            720,
            520,
        )

        self.resize(
            780,
            600,
        )

        self._setup_ui()
        self._apply_style()

    def _setup_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        root_layout.setSpacing(
            Metrics.SPACING_LARGE
        )

        title_label = QLabel(
            "Datenqualität"
        )

        title_label.setObjectName(
            "DataQualityDialogTitle"
        )

        title_label.setFont(
            Typography.title()
        )

        subtitle_label = QLabel(
            (
                f"{self.quality.competition_name} · "
                f"{self.quality.season_name}"
            )
        )

        subtitle_label.setObjectName(
            "DataQualityDialogSubtitle"
        )

        subtitle_label.setFont(
            Typography.body()
        )

        root_layout.addWidget(
            title_label
        )

        root_layout.addWidget(
            subtitle_label
        )

        summary = QFrame()

        summary.setObjectName(
            "DataQualitySummary"
        )

        summary_layout = QHBoxLayout(
            summary
        )

        summary_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        summary_layout.setSpacing(
            Metrics.SPACING_LARGE
        )

        quality_block = self._summary_block(
            "Kernqualität",
            self._quality_value_text(),
        )

        detail_block = self._summary_block(
            "Detailtiefe",
            self._detail_value_text(),
        )

        source_block = self._summary_block(
            "Quelle",
            self.quality.source_text,
        )

        status_block = self._summary_block(
            "Datenstand",
            self.quality.data_status_text,
        )

        summary_layout.addWidget(
            quality_block,
            1,
        )

        summary_layout.addWidget(
            detail_block,
            1,
        )

        summary_layout.addWidget(
            source_block,
            1,
        )

        summary_layout.addWidget(
            status_block,
            1,
        )

        root_layout.addWidget(
            summary
        )

        explanation = QLabel(
            (
                "Die Bewertung misst die Abdeckung der "
                "vorhandenen Daten. Sie bewertet nicht, "
                "ob die externe Quelle inhaltlich fehlerfrei ist."
            )
        )

        explanation.setObjectName(
            "DataQualityExplanation"
        )

        explanation.setWordWrap(
            True
        )

        root_layout.addWidget(
            explanation
        )

        scroll = QScrollArea()

        scroll.setObjectName(
            "DataQualityScroll"
        )

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        container = QWidget()

        container.setObjectName(
            "DataQualityContainer"
        )

        content_layout = QVBoxLayout(
            container
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        if self.quality.metrics:
            for metric in self.quality.metrics:
                content_layout.addWidget(
                    self._create_metric_row(
                        metric
                    )
                )
        else:
            empty_label = QLabel(
                "Für diesen Wettbewerb sind keine "
                "bewertbaren Qualitätsmetriken vorhanden."
            )

            empty_label.setObjectName(
                "DataQualityEmpty"
            )

            empty_label.setWordWrap(
                True
            )

            content_layout.addWidget(
                empty_label
            )

        content_layout.addStretch(
            1
        )

        scroll.setWidget(
            container
        )

        root_layout.addWidget(
            scroll,
            1,
        )

        footer_layout = QHBoxLayout()

        footer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        footer_layout.addStretch(
            1
        )

        close_button = QPushButton(
            "Schließen"
        )

        close_button.setObjectName(
            "DataQualityCloseButton"
        )

        close_button.setMinimumWidth(
            110
        )

        close_button.clicked.connect(
            self.accept
        )

        footer_layout.addWidget(
            close_button
        )

        root_layout.addLayout(
            footer_layout
        )

    def _summary_block(
        self,
        label_text: str,
        value_text: str,
    ) -> QWidget:
        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            Metrics.SPACING_XXS
        )

        label = QLabel(
            label_text
        )

        label.setObjectName(
            "DataQualitySummaryLabel"
        )

        label.setFont(
            Typography.small()
        )

        value = QLabel(
            value_text
        )

        value.setObjectName(
            "DataQualitySummaryValue"
        )

        value.setFont(
            Typography.heading()
        )

        value.setWordWrap(
            True
        )

        layout.addWidget(
            label
        )

        layout.addWidget(
            value
        )

        return widget

    def _create_metric_row(
        self,
        metric: DataQualityMetric,
    ) -> QFrame:
        frame = QFrame()

        frame.setObjectName(
            "DataQualityMetric"
        )

        frame_layout = QVBoxLayout(
            frame
        )

        frame_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        frame_layout.setSpacing(
            Metrics.SPACING_XS
        )

        top_row = QHBoxLayout()

        top_row.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        label = QLabel(
            metric.label
        )

        label.setObjectName(
            "DataQualityMetricLabel"
        )

        label.setFont(
            Typography.heading()
        )

        top_row.addWidget(
            label
        )

        top_row.addStretch(
            1
        )

        value_label = QLabel(
            self._metric_value_text(
                metric
            )
        )

        value_label.setObjectName(
            "DataQualityMetricValue"
        )

        value_label.setProperty(
            "qualityLevel",
            self._metric_level(
                metric
            ),
        )

        value_label.setFont(
            Typography.body()
        )

        top_row.addWidget(
            value_label
        )

        frame_layout.addLayout(
            top_row
        )

        progress = QProgressBar()

        progress.setObjectName(
            "DataQualityProgress"
        )

        progress.setTextVisible(
            False
        )

        progress.setRange(
            0,
            100,
        )

        progress.setValue(
            int(
                round(
                    metric.percent
                    if metric.percent is not None
                    else 0.0
                )
            )
        )

        progress.setProperty(
            "qualityLevel",
            self._metric_level(
                metric
            ),
        )

        progress.setFixedHeight(
            8
        )

        frame_layout.addWidget(
            progress
        )

        detail_text = (
            f"{metric.available} / {metric.expected}"
            if metric.expected > 0
            else "Nicht bewertbar"
        )

        if metric.note:
            detail_text += (
                f" · {metric.note}"
            )

        detail_label = QLabel(
            detail_text
        )

        detail_label.setObjectName(
            "DataQualityMetricNote"
        )

        detail_label.setWordWrap(
            True
        )

        frame_layout.addWidget(
            detail_label
        )

        return frame

    def _detail_value_text(
        self,
    ) -> str:
        if self.quality.detail_percent is None:
            return "Nicht bewertet"

        return (
            f"{self.quality.detail_percent:.0f} %"
        )

    def _quality_value_text(
        self,
    ) -> str:
        if self.quality.overall_percent is None:
            return "Nicht bewertet"

        return (
            f"{self.quality.overall_percent:.0f} %"
            f" · {self.quality.quality_label}"
        )

    @staticmethod
    def _metric_value_text(
        metric: DataQualityMetric,
    ) -> str:
        if metric.percent is None:
            return "Nicht bewertet"

        return (
            f"{metric.percent:.0f} %"
        )

    @staticmethod
    def _metric_level(
        metric: DataQualityMetric,
    ) -> str:
        if metric.percent is None:
            return "unknown"

        if metric.percent >= 90.0:
            return "good"

        if metric.percent >= 70.0:
            return "medium"

        return "poor"

    def _apply_style(
        self,
    ) -> None:
        self.setStyleSheet(
            f"""
            QDialog#DataQualityDialog {{
                background-color:
                    {Colors.BACKGROUND};
                color:
                    {Colors.TEXT_PRIMARY};
            }}

            QLabel#DataQualityDialogTitle {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
            }}

            QLabel#DataQualityDialogSubtitle,
            QLabel#DataQualityExplanation,
            QLabel#DataQualityMetricNote,
            QLabel#DataQualitySummaryLabel,
            QLabel#DataQualityEmpty {{
                color:
                    {Colors.TEXT_SECONDARY};
                background:
                    transparent;
            }}

            QFrame#DataQualitySummary,
            QFrame#DataQualityMetric {{
                background-color:
                    {Colors.CARD_BACKGROUND};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_LARGE}px;
            }}

            QLabel#DataQualitySummaryValue,
            QLabel#DataQualityMetricLabel {{
                color:
                    {Colors.TEXT_PRIMARY};
                background:
                    transparent;
            }}

            QLabel#DataQualityMetricValue {{
                background:
                    transparent;
            }}

            QLabel#DataQualityMetricValue[qualityLevel="good"] {{
                color:
                    {Colors.SUCCESS};
            }}

            QLabel#DataQualityMetricValue[qualityLevel="medium"] {{
                color:
                    {Colors.WARNING};
            }}

            QLabel#DataQualityMetricValue[qualityLevel="poor"] {{
                color:
                    {Colors.ERROR};
            }}

            QLabel#DataQualityMetricValue[qualityLevel="unknown"] {{
                color:
                    {Colors.TEXT_MUTED};
            }}

            QScrollArea#DataQualityScroll,
            QWidget#DataQualityContainer {{
                background:
                    transparent;
                border:
                    none;
            }}

            QProgressBar#DataQualityProgress {{
                background-color:
                    {Colors.BACKGROUND_ELEVATED};
                border:
                    none;
                border-radius:
                    4px;
            }}

            QProgressBar#DataQualityProgress::chunk {{
                background-color:
                    {Colors.PRIMARY};
                border-radius:
                    4px;
            }}

            QProgressBar#DataQualityProgress[qualityLevel="good"]::chunk {{
                background-color:
                    {Colors.SUCCESS};
            }}

            QProgressBar#DataQualityProgress[qualityLevel="medium"]::chunk {{
                background-color:
                    {Colors.WARNING};
            }}

            QProgressBar#DataQualityProgress[qualityLevel="poor"]::chunk {{
                background-color:
                    {Colors.ERROR};
            }}

            QPushButton#DataQualityCloseButton {{
                min-height:
                    34px;
                padding:
                    0 14px;
                color:
                    {Colors.TEXT_PRIMARY};
                background-color:
                    {Colors.CARD_BACKGROUND_ACTIVE};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
            }}

            QPushButton#DataQualityCloseButton:hover {{
                background-color:
                    {Colors.PRIMARY};
                color:
                    {Colors.TEXT_ON_PRIMARY};
            }}
            """
        )
