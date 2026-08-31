from __future__ import annotations

from PySide6.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.windows.competition_tabs.away_table_tab import (
    CompetitionAwayTableTab,
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
from src.ui.windows.competition_tabs.goal_timeline_tab import (
    CompetitionGoalTimelineTab,
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
from src.ui.windows.competition_tabs.progress_tab import (
    CompetitionProgressTab,
)
from src.ui.windows.competition_tabs.result_distribution_tab import (
    CompetitionResultDistributionTab,
)
from src.ui.windows.competition_tabs.statistics_tab import (
    CompetitionStatisticsTab,
)
from src.ui.windows.competition_tabs.streaks_tab import (
    CompetitionStreaksTab,
)


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

        self.home_away_tab = (
            CompetitionHomeAwayTab()
        )

        self.comparison_tab = (
            CompetitionComparisonTab()
        )

        self.head_to_head_tab = (
            CompetitionHeadToHeadTab()
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

        self.register_tab(
            self.home_tab,
            "Heim",
        )

        self.register_tab(
            self.away_tab,
            "Auswärts",
        )

        self.register_tab(
            self.form_tab,
            "Form",
        )

        self.register_tab(
            self.progress_tab,
            "Verlauf",
        )

        self.register_tab(
            self.streaks_tab,
            "Serien",
        )

        self.register_tab(
            self.result_distribution_tab,
            "Ergebnisse",
        )

        self.register_tab(
            self.home_away_tab,
            "Heim/Auswärts",
        )

        self.register_tab(
            self.comparison_tab,
            "Vergleich",
        )

        self.register_tab(
            self.head_to_head_tab,
            "Direkte Duelle",
        )

        self.register_tab(
            self.top_scorer_tab,
            "Torjäger",
        )

        self.register_tab(
            self.fairplay_tab,
            "Fairplay",
        )

        self.register_tab(
            self.goal_timeline_tab,
            "Torphasen",
        )

        layout.addWidget(
            self.tabs,
            1,
        )

    def register_tab(
        self,
        tab: QWidget,
        title: str,
    ) -> None:
        self.tabs.addTab(
            tab,
            title,
        )

        self.statistic_tabs.append(
            tab
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