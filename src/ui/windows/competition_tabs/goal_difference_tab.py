from __future__ import annotations

import sqlite3

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)

from src.services.statistics.goal_difference_service import (
    GoalDifferenceService,
)
from src.ui.windows.competition_tabs.base_statistics_tab import (
    BaseStatisticsTab,
)


class GoalDifferenceDivergingChart(QWidget):
    POSITIVE_COLOR = QColor("#2f9e44")
    NEGATIVE_COLOR = QColor("#d94848")
    NEUTRAL_COLOR = QColor("#7a8088")

    BACKGROUND_COLOR = QColor("#f7f7f7")
    TEXT_COLOR = QColor("#202124")
    MUTED_TEXT_COLOR = QColor("#6b6f76")
    GRID_COLOR = QColor("#d9dde2")
    ZERO_LINE_COLOR = QColor("#767b82")

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.teams: list[dict] = []

        self.setMinimumHeight(
            330
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_data(
        self,
        teams: list[dict],
    ) -> None:
        self.teams = sorted(
            teams,
            key=lambda team: int(
                team["goal_difference"]
            ),
            reverse=True,
        )

        self.update()

    def clear_data(
        self,
    ) -> None:
        self.teams = []
        self.update()

    def paintEvent(
        self,
        event,
    ) -> None:
        super().paintEvent(
            event
        )

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        outer = QRectF(
            4,
            4,
            max(
                0,
                self.width() - 8
            ),
            max(
                0,
                self.height() - 8
            ),
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            self.BACKGROUND_COLOR
        )

        painter.drawRoundedRect(
            outer,
            7,
            7,
        )

        if not self.teams:
            self._draw_empty_state(
                painter
            )
            return

        self._draw_chart(
            painter
        )

    def _draw_empty_state(
        self,
        painter: QPainter,
    ) -> None:
        font = QFont(
            painter.font()
        )
        font.setPointSize(
            11
        )

        painter.setFont(
            font
        )

        painter.setPen(
            self.MUTED_TEXT_COLOR
        )

        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Keine Daten vorhanden",
        )

    def _draw_chart(
        self,
        painter: QPainter,
    ) -> None:
        width = self.width()
        height = self.height()

        title_font = QFont(
            painter.font()
        )
        title_font.setPointSize(
            10
        )
        title_font.setBold(
            True
        )

        painter.setFont(
            title_font
        )

        painter.setPen(
            self.TEXT_COLOR
        )

        painter.drawText(
            QRectF(
                20,
                8,
                width - 40,
                22,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "Tordifferenz nach Mannschaft",
        )

        subtitle_font = QFont(
            painter.font()
        )
        subtitle_font.setPointSize(
            8
        )
        subtitle_font.setBold(
            False
        )

        painter.setFont(
            subtitle_font
        )

        painter.setPen(
            self.MUTED_TEXT_COLOR
        )

        painter.drawText(
            QRectF(
                20,
                30,
                width - 40,
                16,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "Grün = positive Tordifferenz · Rot = negative Tordifferenz",
        )

        left_margin = 185
        right_margin = 62
        top = 60
        bottom = 22

        plot_left = float(
            left_margin
        )
        plot_right = float(
            max(
                left_margin + 120,
                width - right_margin,
            )
        )

        plot_top = float(
            top
        )
        plot_bottom = float(
            max(
                top + 80,
                height - bottom,
            )
        )

        zero_x = (
            plot_left
            + (
                plot_right
                - plot_left
            )
            / 2
        )

        values = [
            int(
                team["goal_difference"]
            )
            for team in self.teams
        ]

        max_abs = max(
            1,
            max(
                abs(value)
                for value in values
            ),
        )

        half_width = (
            plot_right
            - plot_left
        ) / 2

        row_height = (
            plot_bottom
            - plot_top
        ) / max(
            1,
            len(self.teams)
        )

        self._draw_scale(
            painter=painter,
            plot_left=plot_left,
            plot_right=plot_right,
            zero_x=zero_x,
            plot_top=plot_top,
            plot_bottom=plot_bottom,
            max_abs=max_abs,
        )

        team_font = QFont(
            painter.font()
        )

        team_font_size = 8

        if row_height < 23:
            team_font_size = 7

        if row_height < 19:
            team_font_size = 6

        team_font.setPointSize(
            team_font_size
        )

        painter.setFont(
            team_font
        )

        metrics = QFontMetrics(
            team_font
        )

        for index, team in enumerate(
            self.teams
        ):
            value = int(
                team["goal_difference"]
            )

            center_y = (
                plot_top
                + row_height
                * (
                    index
                    + 0.5
                )
            )

            bar_height = min(
                16.0,
                max(
                    6.0,
                    row_height * 0.58,
                ),
            )

            team_name = str(
                team["team_name"]
            )

            team_text = metrics.elidedText(
                team_name,
                Qt.TextElideMode.ElideRight,
                left_margin - 28,
            )

            painter.setPen(
                self.TEXT_COLOR
            )

            painter.drawText(
                QRectF(
                    18,
                    center_y - row_height / 2,
                    left_margin - 32,
                    row_height,
                ),
                (
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                ),
                team_text,
            )

            bar_length = (
                abs(value)
                / max_abs
                * (
                    half_width
                    - 18
                )
            )

            if value > 0:
                bar_rect = QRectF(
                    zero_x,
                    center_y - bar_height / 2,
                    bar_length,
                    bar_height,
                )
                bar_color = (
                    self.POSITIVE_COLOR
                )
            elif value < 0:
                bar_rect = QRectF(
                    zero_x - bar_length,
                    center_y - bar_height / 2,
                    bar_length,
                    bar_height,
                )
                bar_color = (
                    self.NEGATIVE_COLOR
                )
            else:
                bar_rect = QRectF(
                    zero_x - 2,
                    center_y - bar_height / 2,
                    4,
                    bar_height,
                )
                bar_color = (
                    self.NEUTRAL_COLOR
                )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.setBrush(
                bar_color
            )

            painter.drawRoundedRect(
                bar_rect,
                3,
                3,
            )

            value_text = (
                f"{value:+d}"
                if value != 0
                else "0"
            )

            painter.setPen(
                self.TEXT_COLOR
            )

            if value > 0:
                value_rect = QRectF(
                    bar_rect.right() + 7,
                    center_y - row_height / 2,
                    48,
                    row_height,
                )
                alignment = (
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                )
            elif value < 0:
                value_rect = QRectF(
                    bar_rect.left() - 55,
                    center_y - row_height / 2,
                    48,
                    row_height,
                )
                alignment = (
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignRight
                )
            else:
                value_rect = QRectF(
                    zero_x + 7,
                    center_y - row_height / 2,
                    40,
                    row_height,
                )
                alignment = (
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                )

            painter.drawText(
                value_rect,
                alignment,
                value_text,
            )

    def _draw_scale(
        self,
        painter: QPainter,
        plot_left: float,
        plot_right: float,
        zero_x: float,
        plot_top: float,
        plot_bottom: float,
        max_abs: int,
    ) -> None:
        half_width = (
            plot_right
            - plot_left
        ) / 2

        grid_pen = QPen(
            self.GRID_COLOR
        )
        grid_pen.setWidthF(
            1.0
        )

        painter.setPen(
            grid_pen
        )

        for fraction in (
            0.5,
            1.0,
        ):
            offset = (
                half_width
                * fraction
            )

            painter.drawLine(
                int(
                    zero_x - offset
                ),
                int(
                    plot_top
                ),
                int(
                    zero_x - offset
                ),
                int(
                    plot_bottom
                ),
            )

            painter.drawLine(
                int(
                    zero_x + offset
                ),
                int(
                    plot_top
                ),
                int(
                    zero_x + offset
                ),
                int(
                    plot_bottom
                ),
            )

        zero_pen = QPen(
            self.ZERO_LINE_COLOR
        )
        zero_pen.setWidthF(
            1.6
        )

        painter.setPen(
            zero_pen
        )

        painter.drawLine(
            int(
                zero_x
            ),
            int(
                plot_top
            ),
            int(
                zero_x
            ),
            int(
                plot_bottom
            ),
        )

        axis_font = QFont(
            painter.font()
        )
        axis_font.setPointSize(
            7
        )

        painter.setFont(
            axis_font
        )

        painter.setPen(
            self.MUTED_TEXT_COLOR
        )

        labels = [
            (
                plot_left,
                f"-{max_abs}",
            ),
            (
                zero_x,
                "0",
            ),
            (
                plot_right,
                f"+{max_abs}",
            ),
        ]

        for x_position, text in labels:
            painter.drawText(
                QRectF(
                    x_position - 30,
                    plot_bottom + 2,
                    60,
                    16,
                ),
                Qt.AlignmentFlag.AlignCenter,
                text,
            )


class CompetitionGoalDifferenceTab(
    BaseStatisticsTab
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            title="⚖️ Torverhältnis",
            refresh_button_text=(
                "🔄 Torverhältnis aktualisieren"
            ),
        )

        self.chart_widget = (
            GoalDifferenceDivergingChart()
        )

        self.add_content_widget(
            self.chart_widget,
            stretch=1,
        )

        self.clear_data()

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        self.chart_widget.clear_data()

        try:
            with self.database_connection() as connection:
                competition_name = (
                    self.get_competition_name(
                        connection
                    )
                )

                if competition_name is None:
                    self.clear_data()
                    return

                service = GoalDifferenceService(
                    connection
                )

                teams = (
                    service.get_goal_differences(
                        self.competition_id
                    )
                )

                self.chart_widget.set_data(
                    teams
                )

                if teams:
                    best_team = max(
                        teams,
                        key=lambda team: int(
                            team["goal_difference"]
                        ),
                    )

                    worst_team = min(
                        teams,
                        key=lambda team: int(
                            team["goal_difference"]
                        ),
                    )

                    best_value = int(
                        best_team["goal_difference"]
                    )

                    worst_value = int(
                        worst_team["goal_difference"]
                    )

                    self.set_info_text(
                        f"{competition_name} | "
                        f"{len(teams)} Mannschaften | "
                        f"🟢 Beste Tordifferenz: "
                        f"{best_team['team_name']} "
                        f"{best_value:+d} | "
                        f"🔴 Schwächste Tordifferenz: "
                        f"{worst_team['team_name']} "
                        f"{worst_value:+d} | "
                        "Quelle: importierte Spieldaten"
                    )
                else:
                    self.set_info_text(
                        f"{competition_name} | "
                        "Keine Daten | "
                        "Quelle: importierte Spieldaten"
                    )

                self.set_refresh_enabled(
                    True
                )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            self.handle_load_error(
                message=(
                    "Das Torverhältnis konnte "
                    "nicht geladen werden."
                ),
                error=error,
            )

    def clear_content(
        self,
    ) -> None:
        if not hasattr(
            self,
            "chart_widget",
        ):
            return

        self.chart_widget.clear_data()
