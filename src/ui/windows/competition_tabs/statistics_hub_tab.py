from __future__ import annotations

from PySide6.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.windows.competition_tabs.away_table_tab import (
    CompetitionAwayTableTab,
)
from src.ui.windows.competition_tabs.clean_sheet_tab import (
    CompetitionCleanSheetTab,
)
from src.ui.windows.competition_tabs.comparison_tab import (
    CompetitionComparisonTab,
)
from src.ui.windows.competition_tabs.fairplay_tab import (
    CompetitionFairplayTab,
)
from src.ui.windows.competition_tabs.form_tab import (
    CompetitionFormTab,
)
from src.ui.windows.competition_tabs.goal_difference_tab import (
    CompetitionGoalDifferenceTab,
)
from src.ui.windows.competition_tabs.goal_state_tab import (
    CompetitionGoalStateTab,
)
from src.ui.windows.competition_tabs.goal_timeline_tab import (
    CompetitionGoalTimelineTab,
)
from src.ui.windows.competition_tabs.half_goal_tab import (
    CompetitionHalfGoalTab,
)
from src.ui.windows.competition_tabs.halftime_result_tab import (
    CompetitionHalftimeResultTab,
)
from src.ui.windows.competition_tabs.head_to_head_tab import (
    CompetitionHeadToHeadTab,
)
from src.ui.windows.competition_tabs.home_away_tab import (
    CompetitionHomeAwayTab,
)
from src.ui.windows.competition_tabs.home_table_tab import (
    CompetitionHomeTableTab,
)
from src.ui.windows.competition_tabs.lead_comeback_tab import (
    CompetitionLeadComebackTab,
)
from src.ui.windows.competition_tabs.matchday_statistics_tab import (
    CompetitionMatchdayStatisticsTab,
)
from src.ui.windows.competition_tabs.opening_goal_tab import (
    CompetitionOpeningGoalTab,
)
from src.ui.windows.competition_tabs.over_under_tab import (
    CompetitionOverUnderTab,
)
from src.ui.windows.competition_tabs.player_overview_tab import (
    CompetitionPlayerOverviewTab,
)
from src.ui.windows.competition_tabs.progress_tab import (
    CompetitionProgressTab,
)
from src.ui.windows.competition_tabs.records_tab import (
    CompetitionRecordsTab,
)
from src.ui.windows.competition_tabs.result_distribution_tab import (
    CompetitionResultDistributionTab,
)
from src.ui.windows.competition_tabs.result_margin_tab import (
    CompetitionResultMarginTab,
)
from src.ui.windows.competition_tabs.statistics_tab import (
    CompetitionStatisticsTab,
)
from src.ui.windows.competition_tabs.streaks_tab import (
    CompetitionStreaksTab,
)
from src.ui.windows.competition_tabs.team_goal_phase_tab import (
    CompetitionTeamGoalPhaseTab,
)


class StatisticsGroupTab(QWidget):
    def __init__(
        self,
        tabs: list[tuple[QWidget, str]],
    ) -> None:
        super().__init__()

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            0
        )

        self.tabs = QTabWidget()

        self.tabs.setObjectName(
            "CompetitionStatisticsGroupTabs"
        )

        for tab, title in tabs:
            self.tabs.addTab(
                tab,
                title,
            )

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

        layout.addWidget(
            self.tabs,
            1,
        )

    def tab_changed(
        self,
        index: int,
    ) -> None:
        current_tab = self.tabs.widget(
            index
        )

        if current_tab is None:
            return

        if hasattr(
            current_tab,
            "refresh",
        ):
            current_tab.refresh()

    def refresh(
        self,
    ) -> None:
        current_tab = (
            self.tabs.currentWidget()
        )

        if current_tab is None:
            return

        if hasattr(
            current_tab,
            "refresh",
        ):
            current_tab.refresh()


class CompetitionStatisticsHubTab(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.competition_id: int | None = None
        self.statistic_tabs: list[QWidget] = []

        self.setup_ui()
        self.connect_signals()

    def setup_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            0
        )

        self.tabs = QTabWidget()

        self.tabs.setObjectName(
            "CompetitionStatisticsTabs"
        )

        self.create_statistic_tabs()
        self.create_groups()

        layout.addWidget(
            self.tabs,
            1,
        )

    def create_statistic_tabs(
        self,
    ) -> None:
        self.home_tab = (
            CompetitionHomeTableTab()
        )

        self.away_tab = (
            CompetitionAwayTableTab()
        )

        self.form_tab = (
            CompetitionFormTab()
        )

        self.progress_tab = (
            CompetitionProgressTab()
        )

        self.streaks_tab = (
            CompetitionStreaksTab()
        )

        self.result_distribution_tab = (
            CompetitionResultDistributionTab()
        )

        self.clean_sheet_tab = (
            CompetitionCleanSheetTab()
        )

        self.over_under_tab = (
            CompetitionOverUnderTab()
        )

        self.goal_difference_tab = (
            CompetitionGoalDifferenceTab()
        )

        self.team_goal_phase_tab = (
            CompetitionTeamGoalPhaseTab()
        )

        self.result_margin_tab = (
            CompetitionResultMarginTab()
        )

        self.lead_comeback_tab = (
            CompetitionLeadComebackTab()
        )

        self.halftime_result_tab = (
            CompetitionHalftimeResultTab()
        )

        self.half_goal_tab = (
            CompetitionHalfGoalTab()
        )

        self.goal_state_tab = (
            CompetitionGoalStateTab()
        )

        self.opening_goal_tab = (
            CompetitionOpeningGoalTab()
        )

        self.matchday_statistics_tab = (
            CompetitionMatchdayStatisticsTab()
        )

        self.home_away_tab = (
            CompetitionHomeAwayTab()
        )

        self.comparison_tab = (
            CompetitionComparisonTab()
        )

        self.head_to_head_tab = (
            CompetitionHeadToHeadTab()
        )

        self.player_overview_tab = (
            CompetitionPlayerOverviewTab()
        )

        self.top_scorer_tab = (
            CompetitionStatisticsTab()
        )

        self.fairplay_tab = (
            CompetitionFairplayTab()
        )

        self.goal_timeline_tab = (
            CompetitionGoalTimelineTab()
        )

        self.records_tab = (
            CompetitionRecordsTab()
        )

        self.statistic_tabs = [
            self.home_tab,
            self.away_tab,
            self.form_tab,
            self.progress_tab,
            self.streaks_tab,
            self.result_distribution_tab,
            self.clean_sheet_tab,
            self.over_under_tab,
            self.goal_difference_tab,
            self.team_goal_phase_tab,
            self.result_margin_tab,
            self.lead_comeback_tab,
            self.halftime_result_tab,
            self.half_goal_tab,
            self.goal_state_tab,
            self.opening_goal_tab,
            self.matchday_statistics_tab,
            self.home_away_tab,
            self.comparison_tab,
            self.head_to_head_tab,
            self.player_overview_tab,
            self.top_scorer_tab,
            self.fairplay_tab,
            self.goal_timeline_tab,
            self.records_tab,
        ]

    def create_groups(
        self,
    ) -> None:
        self.table_group = StatisticsGroupTab(
            [
                (
                    self.home_tab,
                    "Heim",
                ),
                (
                    self.away_tab,
                    "Auswärts",
                ),
                (
                    self.form_tab,
                    "Form",
                ),
                (
                    self.progress_tab,
                    "Punkteverlauf",
                ),
            ]
        )

        self.results_group = StatisticsGroupTab(
            [
                (
                    self.result_distribution_tab,
                    "Ergebnisse",
                ),
                (
                    self.result_margin_tab,
                    "Siegmargen",
                ),
                (
                    self.clean_sheet_tab,
                    "Zu Null",
                ),
                (
                    self.over_under_tab,
                    "Over/Under",
                ),
            ]
        )

        self.goals_group = StatisticsGroupTab(
            [
                (
                    self.goal_difference_tab,
                    "Übersicht",
                ),
                (
                    self.team_goal_phase_tab,
                    "Früh/Spät",
                ),
                (
                    self.half_goal_tab,
                    "Halbzeiten",
                ),
                (
                    self.goal_state_tab,
                    "Spielstand",
                ),
                (
                    self.opening_goal_tab,
                    "Toreröffnung",
                ),
                (
                    self.goal_timeline_tab,
                    "Torphasen",
                ),
            ]
        )

        self.match_flow_group = StatisticsGroupTab(
            [
                (
                    self.streaks_tab,
                    "Serien",
                ),
                (
                    self.lead_comeback_tab,
                    "Führung/Rückstand",
                ),
                (
                    self.halftime_result_tab,
                    "Halbzeit → Endstand",
                ),
            ]
        )

        self.comparison_group = StatisticsGroupTab(
            [
                (
                    self.home_away_tab,
                    "Heim/Auswärts",
                ),
                (
                    self.comparison_tab,
                    "Mannschaften",
                ),
                (
                    self.head_to_head_tab,
                    "Direkte Duelle",
                ),
            ]
        )

        self.players_group = StatisticsGroupTab(
            [
                (
                    self.player_overview_tab,
                    "Übersicht",
                ),
                (
                    self.top_scorer_tab,
                    "Torjäger",
                ),
                (
                    self.fairplay_tab,
                    "Fairplay",
                ),
            ]
        )

        self.tabs.addTab(
            self.table_group,
            "Tabelle",
        )

        self.tabs.addTab(
            self.results_group,
            "Ergebnisse",
        )

        self.tabs.addTab(
            self.goals_group,
            "Tore",
        )

        self.tabs.addTab(
            self.match_flow_group,
            "Spielverlauf",
        )

        self.tabs.addTab(
            self.matchday_statistics_tab,
            "Spieltage",
        )

        self.tabs.addTab(
            self.comparison_group,
            "Vergleich",
        )

        self.tabs.addTab(
            self.players_group,
            "Spieler",
        )

        self.tabs.addTab(
            self.records_tab,
            "Rekorde",
        )

    def connect_signals(
        self,
    ) -> None:
        self.tabs.currentChanged.connect(
            self.tab_changed
        )

    def set_competition(
        self,
        competition_id: int | None,
    ) -> None:
        self.competition_id = (
            competition_id
        )

        for tab in self.statistic_tabs:
            if hasattr(
                tab,
                "set_competition",
            ):
                tab.set_competition(
                    competition_id
                )

    def tab_changed(
        self,
        index: int,
    ) -> None:
        current_tab = (
            self.tabs.widget(
                index
            )
        )

        if current_tab is None:
            return

        if hasattr(
            current_tab,
            "refresh",
        ):
            current_tab.refresh()

    def refresh(
        self,
    ) -> None:
        current_tab = (
            self.tabs.currentWidget()
        )

        if current_tab is None:
            return

        if hasattr(
            current_tab,
            "refresh",
        ):
            current_tab.refresh()