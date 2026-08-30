from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QFrame,
    QScrollArea,
    QStackedWidget,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QMessageBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.database.repositories.association_repository import AssociationRepository
from src.database.repositories.club_repository import ClubRepository
from src.database.repositories.competition_repository import CompetitionRepository
from src.database.repositories.league_repository import LeagueRepository
from src.database.repositories.match_repository import MatchRepository
from src.database.repositories.season_repository import SeasonRepository
from src.database.repositories.team_repository import TeamRepository
from src.importer.fussballde.importer import FussballDeImporter
from src.services.imports.schedule_import_service import ScheduleImportService
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


class MultiSelectTeamCombo(QComboBox):
    selection_changed = Signal()

    ALL_TEAMS_LABEL = "Alle Mannschaften"

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setFont(
            Typography.body()
        )

        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText(
            self.ALL_TEAMS_LABEL
        )

        self.view().viewport().installEventFilter(
            self
        )
        self.model().dataChanged.connect(
            self._update_display_text
        )

    def set_teams(
        self,
        teams: list[tuple[int, str]],
        selected_ids: set[int] | None = None,
    ) -> None:
        selected_ids = selected_ids or set()

        self.blockSignals(True)
        self.clear()

        self.addItem(
            self.ALL_TEAMS_LABEL,
            None,
        )

        all_item = self.model().item(0)
        all_item.setFlags(
            all_item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        all_item.setData(
            Qt.CheckState.Checked
            if not selected_ids
            else Qt.CheckState.Unchecked,
            Qt.ItemDataRole.CheckStateRole,
        )

        for team_id, team_name in teams:
            self.addItem(
                team_name,
                team_id,
            )

            item = self.model().item(
                self.count() - 1
            )
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setData(
                Qt.CheckState.Checked
                if team_id in selected_ids
                else Qt.CheckState.Unchecked,
                Qt.ItemDataRole.CheckStateRole,
            )

        self.blockSignals(False)
        self._update_display_text()

    def selected_team_ids(
        self,
    ) -> set[int]:
        selected: set[int] = set()

        for index in range(1, self.count()):
            item = self.model().item(index)

            if (
                item.checkState()
                == Qt.CheckState.Checked
            ):
                team_id = self.itemData(index)

                if team_id is not None:
                    selected.add(
                        int(team_id)
                    )

        return selected

    def eventFilter(
        self,
        watched,
        event,
    ) -> bool:
        if (
            watched is self.view().viewport()
            and event.type()
            == QEvent.Type.MouseButtonRelease
        ):
            index = self.view().indexAt(
                event.pos()
            )

            if not index.isValid():
                return False

            row = index.row()

            if row == 0:
                self._select_all_teams()
            else:
                self._toggle_team(row)

            self._update_display_text()
            self.selection_changed.emit()

            return True

        return super().eventFilter(
            watched,
            event,
        )

    def _select_all_teams(self) -> None:
        for index in range(self.count()):
            item = self.model().item(index)
            item.setCheckState(
                Qt.CheckState.Checked
                if index == 0
                else Qt.CheckState.Unchecked
            )

    def _toggle_team(
        self,
        row: int,
    ) -> None:
        item = self.model().item(row)

        item.setCheckState(
            Qt.CheckState.Unchecked
            if item.checkState()
            == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )

        selected = self.selected_team_ids()

        all_item = self.model().item(0)
        all_item.setCheckState(
            Qt.CheckState.Unchecked
            if selected
            else Qt.CheckState.Checked
        )

    def _update_display_text(
        self,
        *args,
    ) -> None:
        selected_ids = self.selected_team_ids()

        if not selected_ids:
            text = self.ALL_TEAMS_LABEL
        elif len(selected_ids) == 1:
            selected_id = next(
                iter(selected_ids)
            )
            text = next(
                (
                    self.itemText(index)
                    for index in range(
                        1,
                        self.count(),
                    )
                    if self.itemData(index)
                    == selected_id
                ),
                "1 Mannschaft ausgewählt",
            )
        else:
            text = (
                f"{len(selected_ids)} Mannschaften ausgewählt"
            )

        self.lineEdit().setText(text)


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
        self.current_view = "month"
        self.year_calendars: list[MatchCalendarWidget] = []

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

        view_layout = QHBoxLayout()
        view_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        view_layout.setSpacing(
            Metrics.SPACING_XXS
        )

        self.day_view_button = QPushButton("Tag")
        self.week_view_button = QPushButton("Woche")
        self.month_view_button = QPushButton("Monat")
        self.year_view_button = QPushButton("Jahr")

        self.view_buttons = {
            "day": self.day_view_button,
            "week": self.week_view_button,
            "month": self.month_view_button,
            "year": self.year_view_button,
        }

        for button in self.view_buttons.values():
            button.setObjectName(
                "CalendarViewButton"
            )
            button.setCheckable(True)
            button.setMinimumWidth(80)
            view_layout.addWidget(button)

        self.month_view_button.setChecked(True)
        view_layout.addStretch()

        root_layout.addLayout(
            view_layout
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

        self.team_filter = MultiSelectTeamCombo()
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

        import_layout = QHBoxLayout()
        import_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        import_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        self.schedule_url_input = QLineEdit()
        self.schedule_url_input.setObjectName(
            "CalendarScheduleUrl"
        )
        self.schedule_url_input.setPlaceholderText(
            "fussball.de Staffel-/Spielplan-URL"
        )
        self.schedule_url_input.setClearButtonEnabled(
            True
        )

        self.schedule_import_button = QPushButton(
            "📥 Staffelspielplan importieren"
        )
        self.schedule_import_button.setObjectName(
            "CalendarScheduleImportButton"
        )

        self.schedule_refresh_button = QPushButton(
            "↻ Spielplan aktualisieren"
        )
        self.schedule_refresh_button.setObjectName(
            "CalendarScheduleRefreshButton"
        )
        self.schedule_refresh_button.setEnabled(
            False
        )

        import_layout.addWidget(
            self.schedule_url_input,
            1,
        )
        import_layout.addWidget(
            self.schedule_import_button
        )
        import_layout.addWidget(
            self.schedule_refresh_button
        )

        root_layout.addLayout(
            import_layout
        )

        self.schedule_sync_label = QLabel(
            "Kein gespeicherter Staffel-Link."
        )
        self.schedule_sync_label.setObjectName(
            "CalendarScheduleSyncLabel"
        )

        root_layout.addWidget(
            self.schedule_sync_label
        )

        self.view_stack = QStackedWidget()
        self.view_stack.setObjectName(
            "CalendarViewStack"
        )

        self.month_page = QWidget()
        self.month_page.setObjectName(
            "CalendarMonthPage"
        )

        content_layout = QHBoxLayout(
            self.month_page
        )
        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
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

        self.day_page = self._create_day_page()
        self.week_page = self._create_week_page()
        self.year_page = self._create_year_page()

        self.view_stack.addWidget(
            self.day_page
        )
        self.view_stack.addWidget(
            self.week_page
        )
        self.view_stack.addWidget(
            self.month_page
        )
        self.view_stack.addWidget(
            self.year_page
        )
        self.view_stack.setCurrentWidget(
            self.month_page
        )

        root_layout.addWidget(
            self.view_stack,
            1,
        )

    def _create_day_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("CalendarDayPage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self.day_title = QLabel()
        self.day_title.setObjectName(
            "CalendarViewTitle"
        )
        self.day_title.setFont(
            Typography.title()
        )

        self.day_scroll = QScrollArea()
        self.day_scroll.setWidgetResizable(True)
        self.day_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.day_container = QWidget()
        self.day_container.setObjectName(
            "CalendarDayContainer"
        )
        self.day_layout = QVBoxLayout(
            self.day_container
        )
        self.day_layout.setContentsMargins(
            0, 0, 0, 0
        )
        self.day_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        self.day_scroll.setWidget(
            self.day_container
        )

        layout.addWidget(self.day_title)
        layout.addWidget(
            self.day_scroll,
            1,
        )

        return page

    def _create_week_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("CalendarWeekPage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self.week_title = QLabel()
        self.week_title.setObjectName(
            "CalendarViewTitle"
        )
        self.week_title.setFont(
            Typography.title()
        )

        self.week_scroll = QScrollArea()
        self.week_scroll.setWidgetResizable(True)
        self.week_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        self.week_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.week_container = QWidget()
        self.week_container.setObjectName(
            "CalendarWeekContainer"
        )
        self.week_layout = QHBoxLayout(
            self.week_container
        )
        self.week_layout.setContentsMargins(
            0, 0, 0, 0
        )
        self.week_layout.setSpacing(
            Metrics.SPACING_SMALL
        )

        self.week_scroll.setWidget(
            self.week_container
        )

        layout.addWidget(self.week_title)
        layout.addWidget(
            self.week_scroll,
            1,
        )

        return page

    def _create_year_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("CalendarYearPage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        self.year_title = QLabel()
        self.year_title.setObjectName(
            "CalendarViewTitle"
        )
        self.year_title.setFont(
            Typography.title()
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.year_container = QWidget()
        self.year_container.setObjectName(
            "CalendarYearContainer"
        )
        self.year_layout = QGridLayout(
            self.year_container
        )
        self.year_layout.setContentsMargins(
            0, 0, 0, 0
        )
        self.year_layout.setSpacing(
            Metrics.SPACING_MEDIUM
        )

        scroll.setWidget(
            self.year_container
        )

        layout.addWidget(self.year_title)
        layout.addWidget(scroll, 1)

        return page

    def _set_calendar_view(
        self,
        view_name: str,
    ) -> None:
        pages = {
            "day": self.day_page,
            "week": self.week_page,
            "month": self.month_page,
            "year": self.year_page,
        }

        if view_name not in pages:
            return

        self.current_view = view_name
        self.view_stack.setCurrentWidget(
            pages[view_name]
        )

        for name, button in (
            self.view_buttons.items()
        ):
            button.setChecked(
                name == view_name
            )

        self._refresh_current_view()

    def _refresh_current_view(self) -> None:
        if self.current_view == "day":
            self._render_day_view()
        elif self.current_view == "week":
            self._render_week_view()
        elif self.current_view == "year":
            self._render_year_view()
        else:
            self._load_month_matches(
                self.calendar.yearShown(),
                self.calendar.monthShown(),
            )
            self._update_selected_date()

    def _navigate_previous(self) -> None:
        if self.current_view == "day":
            self.selected_date = (
                self.selected_date.addDays(-1)
            )
        elif self.current_view == "week":
            self.selected_date = (
                self.selected_date.addDays(-7)
            )
        elif self.current_view == "year":
            self.selected_date = QDate(
                self.selected_date.year() - 1,
                self.selected_date.month(),
                min(
                    self.selected_date.day(),
                    28,
                ),
            )
        else:
            self._show_previous_month()
            return

        self._sync_calendar_to_selected_date()
        self._refresh_current_view()

    def _navigate_next(self) -> None:
        if self.current_view == "day":
            self.selected_date = (
                self.selected_date.addDays(1)
            )
        elif self.current_view == "week":
            self.selected_date = (
                self.selected_date.addDays(7)
            )
        elif self.current_view == "year":
            self.selected_date = QDate(
                self.selected_date.year() + 1,
                self.selected_date.month(),
                min(
                    self.selected_date.day(),
                    28,
                ),
            )
        else:
            self._show_next_month()
            return

        self._sync_calendar_to_selected_date()
        self._refresh_current_view()

    def _sync_calendar_to_selected_date(
        self,
    ) -> None:
        self.calendar.setCurrentPage(
            self.selected_date.year(),
            self.selected_date.month(),
        )
        self.calendar.setSelectedDate(
            self.selected_date
        )

    def _load_matches_between(
        self,
        start_date: QDate,
        end_date: QDate,
    ) -> list:
        if not DATABASE_PATH.exists():
            return []

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            repository = MatchRepository(
                connection
            )
            matches = repository.get_between_dates(
                start_date.toString(
                    "yyyy-MM-dd"
                ),
                end_date.toString(
                    "yyyy-MM-dd"
                ),
            )
        finally:
            connection.close()

        return [
            match
            for match in matches
            if self._match_passes_filters(
                match
            )
        ]

    def _match_passes_filters(
        self,
        match,
    ) -> bool:
        competition_id = (
            self.competition_filter.currentData()
        )
        team_ids = (
            self.team_filter.selected_team_ids()
        )

        if (
            competition_id is not None
            and match.competition_id
            != competition_id
        ):
            return False

        if (
            team_ids
            and match.home_team_id
            not in team_ids
            and match.away_team_id
            not in team_ids
        ):
            return False

        return True

    @staticmethod
    def _clear_layout(
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                CalendarPage._clear_layout(
                    child_layout
                )

    def _render_day_view(self) -> None:
        self._clear_layout(
            self.day_layout
        )

        self.day_title.setText(
            self.selected_date.toString(
                "dddd, dd. MMMM yyyy"
            )
        )

        matches = self._load_matches_between(
            self.selected_date,
            self.selected_date,
        )

        if not matches:
            label = QLabel(
                "Für diesen Tag sind keine "
                "Spiele vorhanden."
            )
            label.setObjectName(
                "CalendarEmptyState"
            )
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            label.setMinimumHeight(220)
            self.day_layout.addWidget(label)
        else:
            matches.sort(
                key=lambda match: (
                    match.kickoff_time or "",
                    match.matchday or 0,
                )
            )

            for match in matches:
                card = self._create_match_card(
                    match
                )
                card.setMaximumWidth(900)

                row = QHBoxLayout()
                row.setContentsMargins(
                    0, 0, 0, 0
                )
                row.addWidget(card, 1)
                row.addStretch(1)

                self.day_layout.addLayout(
                    row
                )

        self.day_layout.addStretch()

    def _week_start_date(self) -> QDate:
        return self.selected_date.addDays(
            1 - self.selected_date.dayOfWeek()
        )

    def _render_week_view(self) -> None:
        self._clear_layout(
            self.week_layout
        )

        start_date = self._week_start_date()
        end_date = start_date.addDays(6)

        self.week_title.setText(
            (
                f"{start_date.toString('dd.MM.yyyy')} "
                f"– {end_date.toString('dd.MM.yyyy')}"
            )
        )

        matches = self._load_matches_between(
            start_date,
            end_date,
        )

        matches_by_date: dict[str, list] = {}

        for match in matches:
            key = (match.match_date or "").strip()

            if key:
                matches_by_date.setdefault(
                    key,
                    [],
                ).append(match)

        for offset in range(7):
            date = start_date.addDays(offset)

            day_frame = QFrame()
            day_frame.setObjectName(
                "CalendarWeekDay"
            )
            day_frame.setMinimumWidth(120)

            day_layout = QVBoxLayout(
                day_frame
            )
            day_layout.setContentsMargins(
                10, 10, 10, 10
            )
            day_layout.setSpacing(
                Metrics.SPACING_SMALL
            )

            day_header = QLabel(
                date.toString(
                    "ddd, dd.MM."
                )
            )
            day_header.setObjectName(
                "CalendarWeekDayTitle"
            )
            day_header.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            day_layout.addWidget(day_header)

            day_matches = matches_by_date.get(
                date.toString(
                    "yyyy-MM-dd"
                ),
                [],
            )
            day_matches.sort(
                key=lambda match: (
                    match.kickoff_time or ""
                )
            )

            if not day_matches:
                empty = QLabel("–")
                empty.setObjectName(
                    "CalendarWeekEmpty"
                )
                empty.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                day_layout.addWidget(empty)
            else:
                for match in day_matches:
                    day_layout.addWidget(
                        self._create_week_match_card(
                            match
                        )
                    )

            day_layout.addStretch()
            self.week_layout.addWidget(
                day_frame,
                1,
            )

    def _create_week_match_card(
        self,
        match,
    ) -> ClickableMatchCard:
        match_id = int(
            getattr(
                match,
                "match_id",
                0,
            )
            or 0
        )

        card = ClickableMatchCard(
            match_id
        )
        card.setObjectName(
            "CalendarWeekMatchCard"
        )
        card.clicked.connect(
            self.match_requested.emit
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            8, 8, 8, 8
        )
        layout.setSpacing(3)

        time_label = QLabel(
            (match.kickoff_time or "--:--")[:5]
        )
        time_label.setObjectName(
            "CalendarWeekMatchTime"
        )

        teams = QLabel(
            (
                f"{match.home_team_name}\n"
                f"{match.away_team_name}"
            )
        )
        teams.setWordWrap(True)
        teams.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
        )
        teams.setObjectName(
            "CalendarWeekMatchTeams"
        )

        result = (
            f"{match.home_goals}:{match.away_goals}"
            if (
                match.home_goals is not None
                and match.away_goals is not None
            )
            else "–"
        )

        result_label = QLabel(result)
        result_label.setObjectName(
            "CalendarWeekMatchResult"
        )

        layout.addWidget(time_label)
        layout.addWidget(teams)
        layout.addWidget(result_label)

        return card

    def _render_year_view(self) -> None:
        self._clear_layout(
            self.year_layout
        )
        self.year_calendars = []

        year = self.selected_date.year()

        self.year_title.setText(
            str(year)
        )

        first_date = QDate(year, 1, 1)
        last_date = QDate(year, 12, 31)

        matches = self._load_matches_between(
            first_date,
            last_date,
        )

        dates_with_matches: set[QDate] = set()

        for match in matches:
            date = QDate.fromString(
                match.match_date or "",
                "yyyy-MM-dd",
            )

            if date.isValid():
                dates_with_matches.add(date)

        for month in range(1, 13):
            wrapper = QFrame()
            wrapper.setObjectName(
                "CalendarYearMonth"
            )

            wrapper_layout = QVBoxLayout(
                wrapper
            )
            wrapper_layout.setContentsMargins(
                8, 8, 8, 8
            )
            wrapper_layout.setSpacing(4)

            title = QLabel(
                QDate(
                    year,
                    month,
                    1,
                ).toString("MMMM")
            )
            title.setObjectName(
                "CalendarYearMonthTitle"
            )

            calendar = MatchCalendarWidget()
            calendar.setObjectName(
                "YearMiniCalendar"
            )
            calendar.setNavigationBarVisible(
                False
            )
            calendar.setGridVisible(False)
            calendar.setVerticalHeaderFormat(
                QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
            )
            calendar.setHorizontalHeaderFormat(
                QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames
            )
            calendar.setCurrentPage(
                year,
                month,
            )
            calendar.setSelectedDate(
                QDate(year, month, 1)
            )

            month_dates = {
                date
                for date in dates_with_matches
                if date.month() == month
            }
            calendar.set_match_dates(
                month_dates
            )

            calendar.clicked.connect(
                self._handle_year_date_clicked
            )

            wrapper_layout.addWidget(title)
            wrapper_layout.addWidget(calendar)

            row = (month - 1) // 3
            column = (month - 1) % 3

            self.year_layout.addWidget(
                wrapper,
                row,
                column,
            )
            self.year_calendars.append(
                calendar
            )

    def _handle_year_date_clicked(
        self,
        date: QDate,
    ) -> None:
        self.selected_date = date
        self._sync_calendar_to_selected_date()
        self._set_calendar_view("day")

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
            self._navigate_previous
        )

        self.next_month_button.clicked.connect(
            self._navigate_next
        )

        self.competition_filter.currentIndexChanged.connect(
            self._handle_competition_filter_changed
        )

        self.team_filter.selection_changed.connect(
            self._apply_filters
        )

        self.schedule_import_button.clicked.connect(
            self._start_schedule_import
        )

        self.schedule_url_input.returnPressed.connect(
            self._start_schedule_import
        )

        self.schedule_refresh_button.clicked.connect(
            self._refresh_selected_schedule
        )

        self.day_view_button.clicked.connect(
            lambda: self._set_calendar_view(
                "day"
            )
        )
        self.week_view_button.clicked.connect(
            lambda: self._set_calendar_view(
                "week"
            )
        )
        self.month_view_button.clicked.connect(
            lambda: self._set_calendar_view(
                "month"
            )
        )
        self.year_view_button.clicked.connect(
            lambda: self._set_calendar_view(
                "year"
            )
        )

    def _load_selected_competition_sync(
        self,
    ) -> None:
        competition_id = (
            self.competition_filter.currentData()
        )

        if competition_id is None:
            self.schedule_refresh_button.setEnabled(
                False
            )
            self.schedule_sync_label.setText(
                "Kein einzelner Wettbewerb ausgewählt."
            )
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            repository = CompetitionRepository(
                connection
            )
            competition = repository.get(
                int(competition_id)
            )
        finally:
            connection.close()

        if competition is None:
            self.schedule_refresh_button.setEnabled(
                False
            )
            self.schedule_sync_label.setText(
                "Wettbewerb konnte nicht geladen werden."
            )
            return

        schedule_url = (
            competition.schedule_url or ""
        ).strip()

        if schedule_url:
            self.schedule_url_input.setText(
                schedule_url
            )
            self.schedule_refresh_button.setEnabled(
                True
            )
        else:
            self.schedule_refresh_button.setEnabled(
                False
            )

        if competition.last_schedule_sync:
            sync_text = (
                competition.last_schedule_sync
                .replace("T", " ")
            )
        else:
            sync_text = "noch nie"

        if schedule_url:
            self.schedule_sync_label.setText(
                f"Letzter Spielplan-Sync: {sync_text}"
            )
        else:
            self.schedule_sync_label.setText(
                "Für diesen Wettbewerb ist noch "
                "kein Staffel-Link gespeichert."
            )

    def _refresh_selected_schedule(
        self,
    ) -> None:
        competition_id = (
            self.competition_filter.currentData()
        )

        if competition_id is None:
            QMessageBox.warning(
                self,
                "Spielplan aktualisieren",
                "Bitte zuerst einen Wettbewerb auswählen.",
            )
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            repository = CompetitionRepository(
                connection
            )
            competition = repository.get(
                int(competition_id)
            )
        finally:
            connection.close()

        if competition is None:
            QMessageBox.warning(
                self,
                "Spielplan aktualisieren",
                "Der Wettbewerb wurde nicht gefunden.",
            )
            return

        schedule_url = (
            competition.schedule_url or ""
        ).strip()

        if not schedule_url:
            QMessageBox.warning(
                self,
                "Spielplan aktualisieren",
                "Für diesen Wettbewerb ist "
                "noch kein Staffel-Link gespeichert.",
            )
            return

        self.schedule_url_input.setText(
            schedule_url
        )
        self._start_schedule_import()

    def _start_schedule_import(
        self,
    ) -> None:
        url = self.schedule_url_input.text().strip()

        if not url:
            QMessageBox.warning(
                self,
                "Spielplan importieren",
                "Bitte eine fussball.de-Spielplan-URL eingeben.",
            )
            return

        if not url.startswith(
            (
                "https://",
                "http://",
            )
        ):
            QMessageBox.warning(
                self,
                "Spielplan importieren",
                "Die URL muss mit http:// oder https:// beginnen.",
            )
            return

        self.schedule_import_button.setEnabled(
            False
        )
        self.schedule_url_input.setEnabled(
            False
        )
        self.schedule_import_button.setText(
            "Import läuft ..."
        )

        start_time = time.perf_counter()

        connection = sqlite3.connect(
            DATABASE_PATH
        )
        connection.row_factory = sqlite3.Row
        connection.execute(
            "PRAGMA foreign_keys = ON;"
        )

        try:
            service = ScheduleImportService(
                association_repository=AssociationRepository(
                    connection
                ),
                league_repository=LeagueRepository(
                    connection
                ),
                season_repository=SeasonRepository(
                    connection
                ),
                club_repository=ClubRepository(
                    connection
                ),
                team_repository=TeamRepository(
                    connection
                ),
                competition_repository=CompetitionRepository(
                    connection
                ),
                match_repository=MatchRepository(
                    connection
                ),
            )

            importer = FussballDeImporter(
                import_service=service
            )

            result = importer.import_schedule(
                url=url,
                headless=True,
                schedule_only=True,
            )

            competition_id = (
                service.last_competition_id
            )

            if competition_id is None:
                raise RuntimeError(
                    "Der importierte Wettbewerb "
                    "konnte nicht ermittelt werden."
                )

            sync_timestamp = (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )

            CompetitionRepository(
                connection
            ).update_schedule_sync(
                competition_id=int(
                    competition_id
                ),
                schedule_url=url,
                last_schedule_sync=(
                    sync_timestamp
                ),
            )

            connection.commit()

            duration = (
                time.perf_counter()
                - start_time
            )

            self.refresh_data()
            self._load_selected_competition_sync()

            QMessageBox.information(
                self,
                "Spielplan importiert",
                (
                    "Der Staffelspielplan wurde erfolgreich importiert.\n\n"
                    f"Neue Spiele: {result.matches_created}\n"
                    f"Aktualisierte Spiele: {result.matches_updated}\n"
                    f"Dauer: {duration:.1f} Sekunden"
                ),
            )

        except Exception as error:
            connection.rollback()

            QMessageBox.critical(
                self,
                "Import fehlgeschlagen",
                (
                    "Der Staffelspielplan konnte nicht importiert werden.\n\n"
                    f"{error}"
                ),
            )

        finally:
            connection.close()

            self.schedule_import_button.setEnabled(
                True
            )
            self.schedule_url_input.setEnabled(
                True
            )
            self.schedule_import_button.setText(
                "📥 Staffelspielplan importieren"
            )

    def _handle_date_selected(self) -> None:
        self.selected_date = (
            self.calendar.selectedDate()
        )

        if self.current_view == "month":
            self._update_selected_date()
        else:
            self._refresh_current_view()

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

        self.selected_date = today
        self._sync_calendar_to_selected_date()

        if self.current_view == "month":
            self._update_selected_date()
        else:
            self._refresh_current_view()

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
        self._load_selected_competition_sync()

    def _refresh_team_filter(self) -> None:
        selected_team_ids = (
            self.team_filter.selected_team_ids()
        )
        competition_id = (
            self.competition_filter.currentData()
        )

        team_names: dict[int, str] = {}

        for match in self.month_matches:
            if (
                competition_id is not None
                and match.competition_id
                != competition_id
            ):
                continue

            if match.home_team_id is not None:
                team_names[
                    int(match.home_team_id)
                ] = match.home_team_name

            if match.away_team_id is not None:
                team_names[
                    int(match.away_team_id)
                ] = match.away_team_name

        available_ids = set(
            team_names.keys()
        )
        selected_team_ids &= available_ids

        teams = sorted(
            team_names.items(),
            key=lambda item: item[1].casefold(),
        )

        self.team_filter.set_teams(
            teams,
            selected_team_ids,
        )

    def _handle_competition_filter_changed(
        self,
    ) -> None:
        self._refresh_team_filter()
        self._load_selected_competition_sync()
        self._apply_filters()

    def _apply_filters(self) -> None:
        competition_id = self.competition_filter.currentData()
        team_ids = (
            self.team_filter.selected_team_ids()
        )

        self.filtered_matches = []

        for match in self.month_matches:
            if (
                competition_id is not None
                and match.competition_id != competition_id
            ):
                continue

            if (
                team_ids
                and match.home_team_id not in team_ids
                and match.away_team_id not in team_ids
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

        if self.current_view == "day":
            self._render_day_view()
        elif self.current_view == "week":
            self._render_week_view()
        elif self.current_view == "year":
            self._render_year_view()

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

            QWidget#CalendarDayPage,
            QWidget#CalendarWeekPage,
            QWidget#CalendarMonthPage,
            QWidget#CalendarYearPage,
            QWidget#CalendarDayContainer,
            QWidget#CalendarWeekContainer,
            QWidget#CalendarYearContainer,
            QStackedWidget#CalendarViewStack {{
                background: transparent;
                border: none;
            }}

            QLabel#CalendarViewTitle,
            QLabel#CalendarWeekDayTitle,
            QLabel#CalendarYearMonthTitle {{
                color: {{Colors.TEXT_PRIMARY}};
                background: transparent;
                border: none;
                font-weight: 700;
            }}

            QPushButton#CalendarViewButton {{
                min-height: 32px;
                padding-left: 12px;
                padding-right: 12px;
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                color: {{Colors.TEXT_SECONDARY}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QPushButton#CalendarViewButton:checked {{
                background-color: {{Colors.PRIMARY}};
                color: {{Colors.TEXT_ON_PRIMARY}};
                border-color: {{Colors.PRIMARY}};
            }}

            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QWidget#CalendarWeekContainer {{
                background: transparent;
            }}

            QFrame#CalendarWeekDay,
            QFrame#CalendarYearMonth {{
                background-color: {{Colors.CARD_BACKGROUND}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QFrame#CalendarWeekMatchCard {{
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_SMALL}}px;
            }}

            QFrame#CalendarWeekMatchCard:hover {{
                border-color: {{Colors.PRIMARY}};
            }}

            QLabel#CalendarWeekMatchTime,
            QLabel#CalendarWeekEmpty {{
                color: {{Colors.TEXT_SECONDARY}};
                background: transparent;
                border: none;
            }}

            QLabel#CalendarWeekMatchTeams,
            QLabel#CalendarWeekMatchResult {{
                color: {{Colors.TEXT_PRIMARY}};
                background: transparent;
                border: none;
            }}

            QLabel#CalendarWeekMatchResult {{
                font-weight: 700;
            }}

            QCalendarWidget#YearMiniCalendar {{
                background-color: transparent;
                color: {{Colors.TEXT_PRIMARY}};
                border: none;
            }}

            QCalendarWidget#YearMiniCalendar QAbstractItemView {{
                background-color: {{Colors.CARD_BACKGROUND}};
                color: {{Colors.TEXT_PRIMARY}};
                selection-background-color: {{Colors.PRIMARY}};
                selection-color: {{Colors.TEXT_ON_PRIMARY}};
                border: none;
                outline: none;
            }}

            QLabel#CalendarScheduleSyncLabel {{
                color: {{Colors.TEXT_SECONDARY}};
                background: transparent;
                border: none;
            }}

            QPushButton#CalendarScheduleRefreshButton {{
                min-height: 36px;
                padding-left: 14px;
                padding-right: 14px;
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                color: {{Colors.TEXT_PRIMARY}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QPushButton#CalendarScheduleRefreshButton:hover:enabled {{
                border-color: {{Colors.PRIMARY}};
            }}

            QLineEdit#CalendarScheduleUrl {{
                min-height: 36px;
                padding-left: 10px;
                padding-right: 10px;
                background-color: {{Colors.CARD_BACKGROUND_ACTIVE}};
                color: {{Colors.TEXT_PRIMARY}};
                border: 1px solid {{Colors.BORDER}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QLineEdit#CalendarScheduleUrl:focus {{
                border-color: {{Colors.PRIMARY}};
            }}

            QPushButton#CalendarScheduleImportButton {{
                min-height: 36px;
                padding-left: 14px;
                padding-right: 14px;
                background-color: {{Colors.PRIMARY}};
                color: {{Colors.TEXT_ON_PRIMARY}};
                border: 1px solid {{Colors.PRIMARY}};
                border-radius: {{Metrics.RADIUS_MEDIUM}}px;
            }}

            QPushButton#CalendarScheduleImportButton:hover {{
                background-color: {{Colors.PRIMARY_HOVER}};
                border-color: {{Colors.PRIMARY_HOVER}};
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