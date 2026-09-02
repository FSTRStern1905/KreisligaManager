from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.statistics.competition_overview_service import (
    CompetitionOverviewService,
)
from src.ui.widgets.info_card import InfoCard


DATABASE_PATH = Path(
    "data/database/kreisligamanager.db"
)


class CompetitionOverviewTab(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competition_id: int | None = None

        self.setup_ui()
        self.clear_data()

    def setup_ui(
        self,
    ) -> None:
        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer_layout.setSpacing(
            0
        )

        header = QWidget()

        header_layout = QVBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            24,
            20,
            24,
            12,
        )

        header_layout.setSpacing(
            8
        )

        title = QLabel(
            "Übersicht"
        )

        title.setObjectName(
            "PageTitle"
        )

        self.competition_name_label = QLabel(
            ""
        )

        self.competition_name_label.setObjectName(
            "InfoLabel"
        )

        header_layout.addWidget(
            title
        )

        header_layout.addWidget(
            self.competition_name_label
        )

        outer_layout.addWidget(
            header
        )

        self.tabs = QTabWidget()

        self.tabs.setObjectName(
            "CompetitionOverviewTabs"
        )

        self.season_tab = self._create_scroll_tab()
        self.records_tab = self._create_scroll_tab()
        self.streaks_tab = self._create_scroll_tab()
        self.data_tab = self._create_scroll_tab()

        season_layout = (
            self.season_tab.widget().layout()
        )

        records_layout = (
            self.records_tab.widget().layout()
        )

        streaks_layout = (
            self.streaks_tab.widget().layout()
        )

        data_layout = (
            self.data_tab.widget().layout()
        )

        self._create_meta_section(
            season_layout
        )

        self._create_kpi_section(
            season_layout
        )

        self._create_result_section(
            season_layout
        )

        self._create_goal_section(
            season_layout
        )

        season_layout.addStretch()

        self._create_record_section(
            records_layout
        )

        self._create_team_record_section(
            records_layout
        )

        records_layout.addStretch()

        self._create_streak_record_section(
            streaks_layout
        )

        streaks_layout.addStretch()

        self._create_card_section(
            data_layout
        )

        self._create_data_section(
            data_layout
        )

        data_layout.addStretch()

        self.tabs.addTab(
            self.season_tab,
            "Saison",
        )

        self.tabs.addTab(
            self.records_tab,
            "Rekorde",
        )

        self.tabs.addTab(
            self.streaks_tab,
            "Serien",
        )

        self.tabs.addTab(
            self.data_tab,
            "Daten",
        )

        outer_layout.addWidget(
            self.tabs,
            1,
        )

    def _create_scroll_tab(
        self,
    ) -> QScrollArea:
        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_area.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        content = QWidget()

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            24,
            16,
            24,
            24,
        )

        layout.setSpacing(
            12
        )

        scroll_area.setWidget(
            content
        )

        return scroll_area

    def _create_meta_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Wettbewerb"
            )
        )

        grid = self._create_grid()

        self.league_card = InfoCard(
            title="Liga",
            value="-",
            icon="🏆",
        )

        self.season_card = InfoCard(
            title="Saison",
            value="-",
            icon="📅",
        )

        self.teams_card = InfoCard(
            title="Mannschaften",
            value="0",
            icon="👕",
        )

        self.matchday_card = InfoCard(
            title="Spieltag",
            value="-",
            icon="📆",
        )

        grid.addWidget(
            self.league_card,
            0,
            0,
        )

        grid.addWidget(
            self.season_card,
            0,
            1,
        )

        grid.addWidget(
            self.teams_card,
            0,
            2,
        )

        grid.addWidget(
            self.matchday_card,
            0,
            3,
        )

        self._equal_columns(
            grid,
            4,
        )

        layout.addLayout(
            grid
        )

    def _create_kpi_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Saison auf einen Blick"
            )
        )

        grid = self._create_grid()

        self.matches_card = InfoCard(
            title="Spiele",
            value="0",
            icon="⚽",
        )

        self.goals_card = InfoCard(
            title="Tore",
            value="0",
            icon="🥅",
        )

        self.goals_per_match_card = InfoCard(
            title="Tore / Spiel",
            value="0.00",
            icon="📊",
        )

        self.import_card = InfoCard(
            title="Detailimport",
            value="0 %",
            icon="📥",
        )

        grid.addWidget(
            self.matches_card,
            0,
            0,
        )

        grid.addWidget(
            self.goals_card,
            0,
            1,
        )

        grid.addWidget(
            self.goals_per_match_card,
            0,
            2,
        )

        grid.addWidget(
            self.import_card,
            0,
            3,
        )

        self._equal_columns(
            grid,
            4,
        )

        layout.addLayout(
            grid
        )

    def _create_result_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Spielausgänge"
            )
        )

        grid = self._create_grid()

        self.home_wins_card = InfoCard(
            title="Heimsiege",
            value="0",
            icon="🏠",
        )

        self.draws_card = InfoCard(
            title="Unentschieden",
            value="0",
            icon="🤝",
        )

        self.away_wins_card = InfoCard(
            title="Auswärtssiege",
            value="0",
            icon="🚌",
        )

        grid.addWidget(
            self.home_wins_card,
            0,
            0,
        )

        grid.addWidget(
            self.draws_card,
            0,
            1,
        )

        grid.addWidget(
            self.away_wins_card,
            0,
            2,
        )

        self._equal_columns(
            grid,
            3,
        )

        layout.addLayout(
            grid
        )

    def _create_goal_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Tore"
            )
        )

        grid = self._create_grid()

        self.home_goals_card = InfoCard(
            title="Heimtore",
            value="0",
            icon="🏠",
        )

        self.away_goals_card = InfoCard(
            title="Auswärtstore",
            value="0",
            icon="🚌",
        )

        self.scorers_card = InfoCard(
            title="Torschützen",
            value="0",
            icon="👤",
        )

        grid.addWidget(
            self.home_goals_card,
            0,
            0,
        )

        grid.addWidget(
            self.away_goals_card,
            0,
            1,
        )

        grid.addWidget(
            self.scorers_card,
            0,
            2,
        )

        self._equal_columns(
            grid,
            3,
        )

        layout.addLayout(
            grid
        )

    def _create_record_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Spielrekorde"
            )
        )

        grid = self._create_grid()

        self.biggest_home_win_card = InfoCard(
            title="Höchster Heimsieg",
            value="-",
            icon="🏠",
        )

        self.biggest_away_win_card = InfoCard(
            title="Höchster Auswärtssieg",
            value="-",
            icon="🚌",
        )

        self.biggest_win_card = InfoCard(
            title="Höchster Sieg",
            value="-",
            icon="🏆",
        )

        self.highest_scoring_match_card = InfoCard(
            title="Torreichstes Spiel",
            value="-",
            icon="🔥",
        )

        grid.addWidget(
            self.biggest_home_win_card,
            0,
            0,
        )

        grid.addWidget(
            self.biggest_away_win_card,
            0,
            1,
        )

        grid.addWidget(
            self.biggest_win_card,
            1,
            0,
        )

        grid.addWidget(
            self.highest_scoring_match_card,
            1,
            1,
        )

        self._equal_columns(
            grid,
            2,
        )

        layout.addLayout(
            grid
        )

    def _create_team_record_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Teamrekorde"
            )
        )

        grid = self._create_grid()

        self.best_offense_card = InfoCard(
            title="Beste Offensive",
            value="-",
            icon="⚽",
        )

        self.best_defense_card = InfoCard(
            title="Beste Defensive",
            value="-",
            icon="🛡️",
        )

        self.most_wins_card = InfoCard(
            title="Meiste Siege",
            value="-",
            icon="🏆",
        )

        self.most_draws_card = InfoCard(
            title="Meiste Unentschieden",
            value="-",
            icon="🤝",
        )

        self.most_losses_card = InfoCard(
            title="Meiste Niederlagen",
            value="-",
            icon="📉",
        )

        self.best_goal_difference_card = InfoCard(
            title="Beste Tordifferenz",
            value="-",
            icon="📈",
        )

        self.worst_offense_card = InfoCard(
            title="Schwächste Offensive",
            value="-",
            icon="🥅",
        )

        self.worst_defense_card = InfoCard(
            title="Schwächste Defensive",
            value="-",
            icon="🚨",
        )

        self.worst_goal_difference_card = InfoCard(
            title="Schlechteste Tordifferenz",
            value="-",
            icon="📉",
        )

        grid.addWidget(
            self.best_offense_card,
            0,
            0,
        )

        grid.addWidget(
            self.best_defense_card,
            0,
            1,
        )

        grid.addWidget(
            self.most_wins_card,
            0,
            2,
        )

        grid.addWidget(
            self.most_draws_card,
            1,
            0,
        )

        grid.addWidget(
            self.most_losses_card,
            1,
            1,
        )

        grid.addWidget(
            self.best_goal_difference_card,
            1,
            2,
        )

        grid.addWidget(
            self.worst_offense_card,
            2,
            0,
        )

        grid.addWidget(
            self.worst_defense_card,
            2,
            1,
        )

        grid.addWidget(
            self.worst_goal_difference_card,
            2,
            2,
        )

        self._equal_columns(
            grid,
            3,
        )

        layout.addLayout(
            grid
        )

    def _create_streak_record_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Serienrekorde"
            )
        )

        grid = self._create_grid()

        self.longest_win_streak_card = InfoCard(
            title="Längste Siegesserie",
            value="-",
            icon="🔥",
        )

        self.longest_unbeaten_streak_card = InfoCard(
            title="Längste Ungeschlagen-Serie",
            value="-",
            icon="🛡️",
        )

        self.longest_loss_streak_card = InfoCard(
            title="Längste Niederlagenserie",
            value="-",
            icon="📉",
        )

        self.longest_winless_streak_card = InfoCard(
            title="Längste Sieglos-Serie",
            value="-",
            icon="⛔",
        )

        self.longest_scoring_streak_card = InfoCard(
            title="Längste Torserie",
            value="-",
            icon="⚽",
        )

        self.longest_clean_sheet_streak_card = InfoCard(
            title="Längste Zu-Null-Serie",
            value="-",
            icon="🧤",
        )

        grid.addWidget(
            self.longest_win_streak_card,
            0,
            0,
        )

        grid.addWidget(
            self.longest_unbeaten_streak_card,
            0,
            1,
        )

        grid.addWidget(
            self.longest_loss_streak_card,
            0,
            2,
        )

        grid.addWidget(
            self.longest_winless_streak_card,
            1,
            0,
        )

        grid.addWidget(
            self.longest_scoring_streak_card,
            1,
            1,
        )

        grid.addWidget(
            self.longest_clean_sheet_streak_card,
            1,
            2,
        )

        self._equal_columns(
            grid,
            3,
        )

        layout.addLayout(
            grid
        )

    def _create_card_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Karten"
            )
        )

        grid = self._create_grid()

        self.cards_card = InfoCard(
            title="Gesamt",
            value="0",
            icon="🃏",
        )

        self.yellow_cards_card = InfoCard(
            title="Gelb",
            value="0",
            icon="🟨",
        )

        self.yellow_red_cards_card = InfoCard(
            title="Gelb-Rot",
            value="0",
            icon="🟧",
        )

        self.red_cards_card = InfoCard(
            title="Rot",
            value="0",
            icon="🟥",
        )

        grid.addWidget(
            self.cards_card,
            0,
            0,
        )

        grid.addWidget(
            self.yellow_cards_card,
            0,
            1,
        )

        grid.addWidget(
            self.yellow_red_cards_card,
            0,
            2,
        )

        grid.addWidget(
            self.red_cards_card,
            0,
            3,
        )

        self._equal_columns(
            grid,
            4,
        )

        layout.addLayout(
            grid
        )

    def _create_data_section(
        self,
        layout: QVBoxLayout,
    ) -> None:
        layout.addWidget(
            self._section_title(
                "Datenstand"
            )
        )

        grid = self._create_grid()

        self.finished_matches_card = InfoCard(
            title="Beendet",
            value="0",
            icon="✅",
        )

        self.scheduled_matches_card = InfoCard(
            title="Ausstehend",
            value="0",
            icon="⏳",
        )

        self.status_card = InfoCard(
            title="Status",
            value="-",
            icon="🟢",
        )

        grid.addWidget(
            self.finished_matches_card,
            0,
            0,
        )

        grid.addWidget(
            self.scheduled_matches_card,
            0,
            1,
        )

        grid.addWidget(
            self.status_card,
            0,
            2,
        )

        self._equal_columns(
            grid,
            3,
        )

        layout.addLayout(
            grid
        )

    @staticmethod
    def _create_grid(
    ) -> QGridLayout:
        grid = QGridLayout()

        grid.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        grid.setHorizontalSpacing(
            8
        )

        grid.setVerticalSpacing(
            8
        )

        return grid

    @staticmethod
    def _equal_columns(
        grid: QGridLayout,
        count: int,
    ) -> None:
        for column in range(
            count
        ):
            grid.setColumnStretch(
                column,
                1,
            )

    @staticmethod
    def _section_title(
        text: str,
    ) -> QLabel:
        label = QLabel(
            text
        )

        label.setObjectName(
            "SectionTitle"
        )

        label.setContentsMargins(
            0,
            6,
            0,
            0,
        )

        return label

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(
        self,
    ) -> None:
        if self.competition_id is None:
            self.clear_data()
            return

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        try:
            service = CompetitionOverviewService(
                connection
            )

            overview = service.get_overview(
                self.competition_id
            )

            self._apply_overview(
                overview
            )

        except (
            sqlite3.Error,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Datenbankfehler",
                (
                    "Wettbewerbsdaten konnten "
                    "nicht geladen werden:\n"
                    f"{error}"
                ),
            )

            self.clear_data()

        finally:
            connection.close()

    def _apply_overview(
        self,
        overview: dict,
    ) -> None:
        status_text = (
            "Aktiv"
            if overview["active"]
            else "Inaktiv"
        )

        self.competition_name_label.setText(
            (
                f"{overview['competition_name']} "
                f"· {status_text}"
            )
        )

        self.league_card.set_value(
            overview["league_name"]
            or "Keine Liga"
        )

        self.season_card.set_value(
            overview["season_name"]
            or "-"
        )

        self.status_card.set_value(
            status_text
        )

        self.teams_card.set_value(
            str(
                overview["team_count"]
            )
        )

        current_matchday = overview[
            "current_matchday"
        ]

        maximum_matchday = overview[
            "maximum_matchday"
        ]

        if (
            current_matchday is not None
            and maximum_matchday is not None
        ):
            matchday_text = (
                f"{current_matchday} / "
                f"{maximum_matchday}"
            )

        elif maximum_matchday is not None:
            matchday_text = (
                f"0 / {maximum_matchday}"
            )

        else:
            matchday_text = "-"

        self.matchday_card.set_value(
            matchday_text
        )

        self.matches_card.set_value(
            str(
                overview["matches_total"]
            )
        )

        self.finished_matches_card.set_value(
            str(
                overview["finished_matches"]
            )
        )

        self.scheduled_matches_card.set_value(
            str(
                overview["scheduled_matches"]
            )
        )

        self.import_card.set_value(
            f"{overview['detail_import_rate']:.1f} %"
        )

        self.goals_card.set_value(
            str(
                overview["goals"]
            )
        )

        self.goals_per_match_card.set_value(
            f"{overview['goals_per_match']:.2f}"
        )

        self.scorers_card.set_value(
            str(
                overview["different_scorers"]
            )
        )

        self.home_goals_card.set_value(
            str(
                overview["home_goals"]
            )
        )

        self.away_goals_card.set_value(
            str(
                overview["away_goals"]
            )
        )

        self.cards_card.set_value(
            str(
                overview["cards_total"]
            )
        )

        self.home_wins_card.set_value(
            (
                f"{overview['home_wins']} "
                f"· {overview['home_win_rate']:.1f} %"
            )
        )

        self.draws_card.set_value(
            (
                f"{overview['draws']} "
                f"· {overview['draw_rate']:.1f} %"
            )
        )

        self.away_wins_card.set_value(
            (
                f"{overview['away_wins']} "
                f"· {overview['away_win_rate']:.1f} %"
            )
        )

        self.yellow_cards_card.set_value(
            str(
                overview["yellow_cards"]
            )
        )

        self.yellow_red_cards_card.set_value(
            str(
                overview["yellow_red_cards"]
            )
        )

        self.red_cards_card.set_value(
            str(
                overview["red_cards"]
            )
        )

        records = overview.get(
            "records",
            {},
        )

        self.biggest_home_win_card.set_value(
            self._format_match_record(
                records.get(
                    "biggest_home_win"
                )
            )
        )

        self.biggest_away_win_card.set_value(
            self._format_match_record(
                records.get(
                    "biggest_away_win"
                )
            )
        )

        self.biggest_win_card.set_value(
            self._format_match_record(
                records.get(
                    "biggest_win"
                )
            )
        )

        self.highest_scoring_match_card.set_value(
            self._format_match_record(
                records.get(
                    "highest_scoring_match"
                )
            )
        )

        self.best_offense_card.set_value(
            self._format_team_record(
                records.get(
                    "best_offense"
                )
            )
        )

        self.best_defense_card.set_value(
            self._format_team_record(
                records.get(
                    "best_defense"
                )
            )
        )

        self.most_wins_card.set_value(
            self._format_team_record(
                records.get(
                    "most_wins"
                )
            )
        )

        self.most_draws_card.set_value(
            self._format_team_record(
                records.get(
                    "most_draws"
                )
            )
        )

        self.most_losses_card.set_value(
            self._format_team_record(
                records.get(
                    "most_losses"
                )
            )
        )

        self.best_goal_difference_card.set_value(
            self._format_team_record(
                records.get(
                    "best_goal_difference"
                ),
                signed=True,
            )
        )

        self.worst_offense_card.set_value(
            self._format_team_record(
                records.get(
                    "worst_offense"
                )
            )
        )

        self.worst_defense_card.set_value(
            self._format_team_record(
                records.get(
                    "worst_defense"
                )
            )
        )

        self.worst_goal_difference_card.set_value(
            self._format_team_record(
                records.get(
                    "worst_goal_difference"
                ),
                signed=True,
            )
        )

        self.longest_win_streak_card.set_value(
            self._format_streak_record(
                records.get(
                    "longest_win_streak"
                )
            )
        )

        self.longest_unbeaten_streak_card.set_value(
            self._format_streak_record(
                records.get(
                    "longest_unbeaten_streak"
                )
            )
        )

        self.longest_loss_streak_card.set_value(
            self._format_streak_record(
                records.get(
                    "longest_loss_streak"
                )
            )
        )

        self.longest_winless_streak_card.set_value(
            self._format_streak_record(
                records.get(
                    "longest_winless_streak"
                )
            )
        )

        self.longest_scoring_streak_card.set_value(
            self._format_streak_record(
                records.get(
                    "longest_scoring_streak"
                )
            )
        )

        self.longest_clean_sheet_streak_card.set_value(
            self._format_streak_record(
                records.get(
                    "longest_clean_sheet_streak"
                )
            )
        )

    @staticmethod
    def _format_match_record(
        record: dict | None,
    ) -> str:
        if not record:
            return "-"

        return (
            f"{record['home_team_name']} "
            f"{record['home_goals']}:"
            f"{record['away_goals']} "
            f"{record['away_team_name']}"
        )

    @staticmethod
    def _format_team_record(
        record: dict | None,
        signed: bool = False,
    ) -> str:
        if not record:
            return "-"

        value = int(
            record["value"]
        )

        if signed:
            value_text = (
                f"{value:+d}"
            )
        else:
            value_text = str(
                value
            )

        return (
            f"{record['team_name']} "
            f"· {value_text}"
        )

    @staticmethod
    def _format_streak_record(
        record: dict | None,
    ) -> str:
        if not record:
            return "-"

        length = int(
            record["length"]
        )

        return (
            f"{record['team_name']} "
            f"· {length} Spiele"
        )

    def refresh(
        self,
    ) -> None:
        self.load_data()

    def clear_data(
        self,
    ) -> None:
        self.competition_name_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.league_card.set_value("-")
        self.season_card.set_value("-")
        self.status_card.set_value("-")

        self.teams_card.set_value("0")
        self.matchday_card.set_value("-")

        self.matches_card.set_value("0")

        self.finished_matches_card.set_value(
            "0"
        )

        self.scheduled_matches_card.set_value(
            "0"
        )

        self.import_card.set_value(
            "0 %"
        )

        self.goals_card.set_value(
            "0"
        )

        self.goals_per_match_card.set_value(
            "0.00"
        )

        self.scorers_card.set_value(
            "0"
        )

        self.home_goals_card.set_value(
            "0"
        )

        self.away_goals_card.set_value(
            "0"
        )

        self.cards_card.set_value(
            "0"
        )

        self.home_wins_card.set_value(
            "0 · 0.0 %"
        )

        self.draws_card.set_value(
            "0 · 0.0 %"
        )

        self.away_wins_card.set_value(
            "0 · 0.0 %"
        )

        self.biggest_home_win_card.set_value(
            "-"
        )

        self.biggest_away_win_card.set_value(
            "-"
        )

        self.biggest_win_card.set_value(
            "-"
        )

        self.highest_scoring_match_card.set_value(
            "-"
        )

        self.best_offense_card.set_value("-")
        self.best_defense_card.set_value("-")
        self.most_wins_card.set_value("-")
        self.most_draws_card.set_value("-")
        self.most_losses_card.set_value("-")
        self.best_goal_difference_card.set_value("-")
        self.worst_offense_card.set_value("-")
        self.worst_defense_card.set_value("-")
        self.worst_goal_difference_card.set_value("-")

        self.longest_win_streak_card.set_value("-")
        self.longest_unbeaten_streak_card.set_value("-")
        self.longest_loss_streak_card.set_value("-")
        self.longest_winless_streak_card.set_value("-")
        self.longest_scoring_streak_card.set_value("-")
        self.longest_clean_sheet_streak_card.set_value("-")

        self.yellow_cards_card.set_value(
            "0"
        )

        self.yellow_red_cards_card.set_value(
            "0"
        )

        self.red_cards_card.set_value(
            "0"
        )