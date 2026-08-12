from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QFrame,
    QScrollArea,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.database.repositories.competition_repository import CompetitionRepository
from src.database.repositories.match_repository import MatchRepository
from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)



class MatchCalendarWidget(QCalendarWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._match_dates: set[QDate] = set()

    def set_match_dates(
        self,
        dates: set[QDate],
    ) -> None:
        self._match_dates = {
            date
            for date in dates
            if date.isValid()
        }

        self.updateCells()

    def paintCell(
        self,
        painter: QPainter,
        rect,
        date: QDate,
    ) -> None:
        super().paintCell(
            painter,
            rect,
            date,
        )

        if date not in self._match_dates:
            return

        painter.save()

        marker_color = QColor(
            Colors.PRIMARY
        )

        if date == self.selectedDate():
            marker_color = QColor(
                Colors.TEXT_ON_PRIMARY
            )

        painter.setPen(
            Qt.PenStyle.NoPen
        )
        painter.setBrush(
            marker_color
        )

        diameter = 6
        x = (
            rect.center().x()
            - diameter // 2
        )
        y = (
            rect.bottom()
            - 10
        )

        painter.drawEllipse(
            x,
            y,
            diameter,
            diameter,
        )

        painter.restore()


class ClickableMatchCard(QFrame):
    clicked = Signal(int)

    def __init__(
        self,
        match_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.match_id = match_id
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
            self.clicked.emit(
                self.match_id
            )

        super().mousePressEvent(event)


class CalendarPage(QWidget):
    match_requested = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("CalendarPage")
        self.selected_date = QDate.currentDate()
        self.month_matches = []
        self.filtered_matches = []
        self.matches_by_date: dict[str, list] = {}
        self.competition_names: dict[int, str] = {}

        self._setup_ui()
        self._connect_signals()
        self._apply_style()
        self._update_selected_date()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )
        root_layout.setSpacing(
            Metrics.SPACING_LARGE
        )

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        header_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        header_text_layout = QVBoxLayout()
        header_text_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        header_text_layout.setSpacing(
            Metrics.SPACING_XXS
        )

        self.title_label = QLabel(
            "Kalender"
        )
        self.title_label.setObjectName(
            "CalendarPageTitle"
        )
        self.title_label.setFont(
            Typography.title()
        )

        self.subtitle_label = QLabel(
            "Spiele und Termine übersichtlich "
            "nach Datum anzeigen."
        )
        self.subtitle_label.setObjectName(
            "CalendarPageSubtitle"
        )
        self.subtitle_label.setFont(
            Typography.body()
        )

        header_text_layout.addWidget(
            self.title_label
        )
        header_text_layout.addWidget(
            self.subtitle_label
        )

        self.previous_month_button = QPushButton(
            "‹"
        )
        self.today_button = QPushButton(
            "Heute"
        )
        self.next_month_button = QPushButton(
            "›"
        )

        self.previous_month_button.setFixedWidth(
            42
        )
        self.next_month_button.setFixedWidth(
            42
        )

        self.previous_month_button.setToolTip(
            "Vorheriger Monat"
        )
        self.today_button.setToolTip(
            "Zum heutigen Datum springen"
        )
        self.next_month_button.setToolTip(
            "Nächster Monat"
        )

        header_layout.addLayout(
            header_text_layout,
            1,
        )
        header_layout.addWidget(
            self.previous_month_button
        )
        header_layout.addWidget(
            self.today_button
        )
        header_layout.addWidget(
            self.next_month_button
        )

        root_layout.addLayout(
            header_layout
        )

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        competition_label = QLabel("Wettbewerb:")
        competition_label.setObjectName(
            "CalendarFilterLabel"
        )

        self.competition_filter = QComboBox()
        self.competition_filter.setObjectName(
            "CalendarFilter"
        )
        self.competition_filter.setMinimumWidth(240)

        team_label = QLabel("Mannschaft:")
        team_label.setObjectName(
            "CalendarFilterLabel"
        )

        self.team_filter = QComboBox()
        self.team_filter.setObjectName(
            "CalendarFilter"
        )
        self.team_filter.setMinimumWidth(240)

        filter_layout.addWidget(competition_label)
        filter_layout.addWidget(self.competition_filter)
        filter_layout.addSpacing(
            Metrics.SPACING_MEDIUM
        )
        filter_layout.addWidget(team_label)
        filter_layout.addWidget(self.team_filter)
        filter_layout.addStretch()

        root_layout.addLayout(filter_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(
            Metrics.SPACING_LARGE
        )

        self.calendar_card = QFrame()
        self.calendar_card.setObjectName(
            "CalendarCard"
        )

        calendar_layout = QVBoxLayout(
            self.calendar_card
        )
        calendar_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        calendar_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self.month_title = QLabel()
        self.month_title.setObjectName(
            "CalendarMonthTitle"
        )
        self.month_title.setFont(
            Typography.title()
        )

        self.calendar = MatchCalendarWidget()
        self.calendar.setObjectName(
            "MainCalendar"
        )
        self.calendar.setGridVisible(
            True
        )
        self.calendar.setNavigationBarVisible(
            False
        )
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setHorizontalHeaderFormat(
            QCalendarWidget.HorizontalHeaderFormat.ShortDayNames
        )
        self.calendar.setSelectedDate(
            self.selected_date
        )

        self._style_calendar_formats()

        calendar_layout.addWidget(
            self.month_title
        )
        calendar_layout.addWidget(
            self.calendar,
            1,
        )

        self.details_card = QFrame()
        self.details_card.setObjectName(
            "CalendarDetailsCard"
        )
        self.details_card.setMinimumWidth(
            500
        )
        self.details_card.setMaximumWidth(
            560
        )

        details_layout = QVBoxLayout(
            self.details_card
        )
        details_layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )
        details_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self.selected_date_title = QLabel()
        self.selected_date_title.setObjectName(
            "SelectedDateTitle"
        )
        self.selected_date_title.setFont(
            Typography.title()
        )

        self.selected_date_subtitle = QLabel()
        self.selected_date_subtitle.setObjectName(
            "SelectedDateSubtitle"
        )
        self.selected_date_subtitle.setFont(
            Typography.body()
        )

        self.games_title = QLabel(
            "Spiele an diesem Tag"
        )
        self.games_title.setObjectName(
            "CalendarSectionTitle"
        )
        self.games_title.setFont(
            Typography.title()
        )

        self.games_scroll = QScrollArea()
        self.games_scroll.setObjectName(
            "CalendarGamesScroll"
        )
        self.games_scroll.setWidgetResizable(
            True
        )
        self.games_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.games_container = QWidget()
        self.games_container.setObjectName(
            "CalendarGamesContainer"
        )

        self.games_layout = QVBoxLayout(
            self.games_container
        )
        self.games_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.games_layout.setSpacing(
            Metrics.SPACING_SMALL
        )
        self.games_layout.addStretch()

        self.games_scroll.setWidget(
            self.games_container
        )

        details_layout.addWidget(
            self.selected_date_title
        )
        details_layout.addWidget(
            self.selected_date_subtitle
        )
        details_layout.addSpacing(
            Metrics.SPACING_SMALL
        )
        details_layout.addWidget(
            self.games_title
        )
        details_layout.addWidget(
            self.games_scroll,
            1,
        )

        content_layout.addWidget(
            self.calendar_card,
            1,
        )
        content_layout.addWidget(
            self.details_card,
            0,
        )

        root_layout.addLayout(
            content_layout,
            1,
        )

    def _connect_signals(self) -> None:
        self.calendar.selectionChanged.connect(
            self._handle_date_selected
        )

        self.calendar.currentPageChanged.connect(
            self._handle_month_changed
        )

        self.today_button.clicked.connect(
            self._go_to_today
        )

        self.previous_month_button.clicked.connect(
            self._show_previous_month
        )

        self.next_month_button.clicked.connect(
            self._show_next_month
        )

        self.competition_filter.currentIndexChanged.connect(
            self._handle_competition_filter_changed
        )

        self.team_filter.currentIndexChanged.connect(
            self._apply_filters
        )

    def _handle_date_selected(self) -> None:
        self.selected_date = (
            self.calendar.selectedDate()
        )

        self._update_selected_date()

    def _handle_month_changed(
        self,
        year: int,
        month: int,
    ) -> None:
        self._update_month_title(
            year,
            month,
        )
        self._load_month_matches(
            year,
            month,
        )

    def _go_to_today(self) -> None:
        today = QDate.currentDate()

        self.calendar.setCurrentPage(
            today.year(),
            today.month(),
        )

        self.calendar.setSelectedDate(
            today
        )

        self.selected_date = today

        self._update_selected_date()

    def _show_previous_month(self) -> None:
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()

        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1

        self.calendar.setCurrentPage(
            year,
            month,
        )

    def _show_next_month(self) -> None:
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

        self.calendar.setCurrentPage(
            year,
            month,
        )

    def _update_selected_date(self) -> None:
        selected = self.selected_date

        self.selected_date_title.setText(
            selected.toString(
                "dddd, dd. MMMM yyyy"
            )
        )

        if selected == QDate.currentDate():
            self.selected_date_subtitle.setText(
                "Heute"
            )
        else:
            self.selected_date_subtitle.setText(
                selected.toString(
                    "dd.MM.yyyy"
                )
            )

        self.calendar.setCurrentPage(
            selected.year(),
            selected.month(),
        )

        self._update_month_title(
            selected.year(),
            selected.month(),
        )
        self._render_selected_date_matches()

    def _update_month_title(
        self,
        year: int,
        month: int,
    ) -> None:
        month_date = QDate(
            year,
            month,
            1,
        )

        self.month_title.setText(
            month_date.toString(
                "MMMM yyyy"
            )
        )

    def refresh_data(self) -> None:
        self._load_month_matches(
            self.calendar.yearShown(),
            self.calendar.monthShown(),
        )
        self._update_selected_date()

    def _load_month_matches(
        self,
        year: int,
        month: int,
    ) -> None:
        first_date = QDate(
            year,
            month,
            1,
        )
        last_date = QDate(
            year,
            month,
            first_date.daysInMonth(),
        )

        self.month_matches = []
        self.matches_by_date = {}

        if not DATABASE_PATH.exists():
            self._clear_match_markers()
            self._render_selected_date_matches()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            repository = MatchRepository(
                connection
            )

            self.month_matches = (
                repository.get_between_dates(
                    first_date.toString(
                        "yyyy-MM-dd"
                    ),
                    last_date.toString(
                        "yyyy-MM-dd"
                    ),
                )
            )
        finally:
            connection.close()

        self._load_competition_names()
        self._refresh_competition_filter()
        self._apply_filters()

    def _load_competition_names(self) -> None:
        self.competition_names = {}

        if not DATABASE_PATH.exists():
            return

        connection = sqlite3.connect(DATABASE_PATH)

        try:
            repository = CompetitionRepository(connection)

            for competition in repository.get_all():
                if competition.competition_id is None:
                    continue

                self.competition_names[
                    int(competition.competition_id)
                ] = competition.name
        finally:
            connection.close()

    def _refresh_competition_filter(self) -> None:
        current_id = self.competition_filter.currentData()

        competition_ids = sorted(
            {
                int(match.competition_id)
                for match in self.month_matches
                if match.competition_id is not None
            },
            key=lambda competition_id: (
                self.competition_names.get(
                    competition_id,
                    str(competition_id),
                ).casefold()
            ),
        )

        self.competition_filter.blockSignals(True)
        self.competition_filter.clear()
        self.competition_filter.addItem(
            "Alle Wettbewerbe",
            None,
        )

        for competition_id in competition_ids:
            self.competition_filter.addItem(
                self.competition_names.get(
                    competition_id,
                    f"Wettbewerb {competition_id}",
                ),
                competition_id,
            )

        if current_id is not None:
            index = self.competition_filter.findData(current_id)
            if index >= 0:
                self.competition_filter.setCurrentIndex(index)

        self.competition_filter.blockSignals(False)
        self._refresh_team_filter()

    def _refresh_team_filter(self) -> None:
        current_team_id = self.team_filter.currentData()
        competition_id = self.competition_filter.currentData()

        team_names: dict[int, str] = {}

        for match in self.month_matches:
            if (
                competition_id is not None
                and match.competition_id != competition_id
            ):
                continue

            if match.home_team_id is not None:
                team_names[int(match.home_team_id)] = (
                    match.home_team_name
                )

            if match.away_team_id is not None:
                team_names[int(match.away_team_id)] = (
                    match.away_team_name
                )

        self.team_filter.blockSignals(True)
        self.team_filter.clear()
        self.team_filter.addItem(
            "Alle Mannschaften",
            None,
        )

        for team_id, team_name in sorted(
            team_names.items(),
            key=lambda item: item[1].casefold(),
        ):
            self.team_filter.addItem(
                team_name,
                team_id,
            )

        if current_team_id is not None:
            index = self.team_filter.findData(current_team_id)
            if index >= 0:
                self.team_filter.setCurrentIndex(index)

        self.team_filter.blockSignals(False)

    def _handle_competition_filter_changed(
        self,
    ) -> None:
        self._refresh_team_filter()
        self._apply_filters()

    def _apply_filters(self) -> None:
        competition_id = self.competition_filter.currentData()
        team_id = self.team_filter.currentData()

        self.filtered_matches = []

        for match in self.month_matches:
            if (
                competition_id is not None
                and match.competition_id != competition_id
            ):
                continue

            if (
                team_id is not None
                and match.home_team_id != team_id
                and match.away_team_id != team_id
            ):
                continue

            self.filtered_matches.append(match)

        self.matches_by_date = {}

        for match in self.filtered_matches:
            match_date = (match.match_date or "").strip()

            if not match_date:
                continue

            self.matches_by_date.setdefault(
                match_date,
                [],
            ).append(match)

        self._apply_match_markers(
            self.calendar.yearShown(),
            self.calendar.monthShown(),
        )
        self._render_selected_date_matches()

    def _apply_match_markers(
        self,
        year: int,
        month: int,
    ) -> None:
        del year
        del month

        match_dates: set[QDate] = set()

        for match_date in self.matches_by_date:
            qdate = QDate.fromString(
                match_date,
                "yyyy-MM-dd",
            )

            if qdate.isValid():
                match_dates.add(
                    qdate
                )

        self.calendar.set_match_dates(
            match_dates
        )

    def _clear_match_markers(
        self,
        year: int | None = None,
        month: int | None = None,
    ) -> None:
        del year
        del month

        self.calendar.set_match_dates(
            set()
        )

    def _render_selected_date_matches(
        self,
    ) -> None:
        while self.games_layout.count():
            item = self.games_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        date_key = self.selected_date.toString(
            "yyyy-MM-dd"
        )

        matches = self.matches_by_date.get(
            date_key,
            [],
        )

        if not matches:
            empty_label = QLabel(
                "Für dieses Datum sind keine "
                "Spiele vorhanden."
            )
            empty_label.setObjectName(
                "CalendarEmptyState"
            )
            empty_label.setWordWrap(
                True
            )
            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            empty_label.setMinimumHeight(
                180
            )

            self.games_layout.addWidget(
                empty_label
            )
            self.games_layout.addStretch()
            return

        for match in matches:
            self.games_layout.addWidget(
                self._create_match_card(
                    match
                )
            )

        self.games_layout.addStretch()

    def _create_match_card(
        self,
        match,
    ) -> QFrame:
        match_id = getattr(
            match,
            "match_id",
            None,
        )

        if match_id is None:
            match_id = getattr(
                match,
                "id",
                0,
            )

        card = ClickableMatchCard(
            int(match_id or 0)
        )
        card.setObjectName(
            "CalendarMatchCard"
        )

        card.clicked.connect(
            self.match_requested.emit
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )
        layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        kickoff = (
            match.kickoff_time or ""
        ).strip()

        if kickoff:
            kickoff = kickoff[:5]
        else:
            kickoff = "--:--"

        matchday = (
            f"{match.matchday}. Spieltag"
            if match.matchday is not None
            else "Spiel"
        )

        meta_label = QLabel(
            f"{kickoff}  ·  {matchday}"
        )
        meta_label.setObjectName(
            "CalendarMatchMeta"
        )

        teams_row = QHBoxLayout()
        teams_row.setSpacing(
            Metrics.SPACING_SMALL
        )

        home_label = QLabel(
            match.home_team_name
        )
        home_label.setObjectName(
            "CalendarMatchHome"
        )
        home_label.setWordWrap(True)
        home_label.setMinimumWidth(150)
        home_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        away_label = QLabel(
            match.away_team_name
        )
        away_label.setObjectName(
            "CalendarMatchAway"
        )
        away_label.setWordWrap(True)
        away_label.setMinimumWidth(150)
        away_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        if (
            match.home_goals is not None
            and match.away_goals is not None
        ):
            result_text = (
                f"{match.home_goals}:"
                f"{match.away_goals}"
            )
        else:
            result_text = "–"

        result_label = QLabel(
            result_text
        )
        result_label.setObjectName(
            "CalendarMatchResult"
        )
        result_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        result_label.setMinimumWidth(64)
        result_label.setMaximumWidth(72)

        teams_row.addWidget(
            home_label,
            1,
        )
        teams_row.addWidget(
            result_label,
            0,
        )
        teams_row.addWidget(
            away_label,
            1,
        )

        status_text = (
            match.status or ""
        ).strip()

        footer_parts: list[str] = []

        if status_text:
            translated_status = {
                "finished": "Beendet",
                "scheduled": "Geplant",
                "cancelled": "Abgesagt",
                "postponed": "Verlegt",
            }.get(
                status_text.casefold(),
                status_text,
            )

            footer_parts.append(
                translated_status
            )

        if match.detail_imported:
            footer_parts.append(
                "Detaildaten vorhanden"
            )

        footer_label = QLabel(
            "  ·  ".join(
                footer_parts
            )
        )
        footer_label.setObjectName(
            "CalendarMatchFooter"
        )
        footer_label.setVisible(
            bool(footer_parts)
        )

        layout.addWidget(
            meta_label
        )
        layout.addLayout(
            teams_row
        )
        layout.addWidget(
            footer_label
        )

        return card

    def _style_calendar_formats(self) -> None:
        weekday_format = QTextCharFormat()
        weekday_format.setForeground(
            QColor(Colors.TEXT_PRIMARY)
        )

        weekend_format = QTextCharFormat()
        weekend_format.setForeground(
            QColor(Colors.TEXT_SECONDARY)
        )

        for day in (
            Qt.DayOfWeek.Monday,
            Qt.DayOfWeek.Tuesday,
            Qt.DayOfWeek.Wednesday,
            Qt.DayOfWeek.Thursday,
            Qt.DayOfWeek.Friday,
        ):
            self.calendar.setWeekdayTextFormat(
                day,
                weekday_format,
            )

        for day in (
            Qt.DayOfWeek.Saturday,
            Qt.DayOfWeek.Sunday,
        ):
            self.calendar.setWeekdayTextFormat(
                day,
                weekend_format,
            )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#CalendarPage {{
                background-color: {{Colors.BACKGROUND}};
            }}

            QLabel#CalendarPageTitle,
            QLabel#CalendarMonthTitle,
            QLabel#SelectedDateTitle,
            QLabel#CalendarSectionTitle {{
                color: {{Colors.TEXT_PRIMARY}};
                background: transparent;
                border: none;
            }}

            QLabel#CalendarPageSubtitle,
            QLabel#SelectedDateSubtitle {{
                color: {{Colors.TEXT_SECONDARY}};
                background: transparent;
                border: none;
            }}

            QFrame#CalendarCard,
            QFrame#CalendarDetailsCard {{
                background-color: {{Colors.CARD_BACKGROUND}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_LARGE}}px;
            }}

            QLabel#CalendarEmptyState {{
                color: {{Colors.TEXT_SECONDARY}};
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
                padding: 24px;
            }}

            QScrollArea#CalendarGamesScroll,
            QWidget#CalendarGamesContainer {{
                background: transparent;
                border: none;
            }}

            QFrame#CalendarMatchCard {{
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
                margin-bottom: 4px;
            }}

            QLabel#CalendarMatchMeta {{
                color: {{Colors.TEXT_SECONDARY}};
                background: transparent;
                border: none;
            }}

            QLabel#CalendarMatchHome,
            QLabel#CalendarMatchAway {{
                color: {{Colors.TEXT_PRIMARY}};
                background: transparent;
                border: none;
            }}

            QLabel#CalendarMatchResult {{
                color: {{Colors.TEXT_PRIMARY}};
                background-color: {{Colors.CARD_BACKGROUND}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_SMALL}}px;
                padding: 8px 10px;
                font-weight: 700;
            }}

            QLabel#CalendarMatchFooter {{
                color: {{Colors.TEXT_SECONDARY}};
                background: transparent;
                border: none;
            }}

            QLabel#CalendarFilterLabel {{
                color: {{Colors.TEXT_SECONDARY}};
                background: transparent;
                border: none;
            }}

            QComboBox#CalendarFilter {{
                min-height: 34px;
                padding-left: 10px;
                padding-right: 10px;
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                color: {{Colors.TEXT_PRIMARY}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QComboBox#CalendarFilter QAbstractItemView {{
                background-color: {{Colors.CARD_BACKGROUND}};
                color: {{Colors.TEXT_PRIMARY}};
                border: 1px solid {{Colors.BORDER}};
                selection-background-color: {{Colors.PRIMARY}};
                selection-color: {{Colors.TEXT_ON_PRIMARY}};
            }}

            QPushButton {{
                min-height: 34px;
                padding-left: 14px;
                padding-right: 14px;
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                color: {{Colors.TEXT_PRIMARY}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QPushButton:hover {{
                background-color: {{Colors.PRIMARY}};
                color: {{Colors.TEXT_ON_PRIMARY}};
                border-color: {{Colors.PRIMARY}};
            }}

            QCalendarWidget#MainCalendar {{
                background-color: transparent;
                color: {{Colors.TEXT_PRIMARY}};
                border: none;
            }}

            QCalendarWidget#MainCalendar QAbstractItemView {{
                background-color: {{Colors.CARD_BACKGROUND}};
                color: {{Colors.TEXT_PRIMARY}};
                selection-background-color: {{Colors.PRIMARY}};
                selection-color: {{Colors.TEXT_ON_PRIMARY}};
                border: none;
                outline: none;
                gridline-color: {{Colors.BORDER}};
            }}
            """
        )