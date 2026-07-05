from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel

from src.database.repository import Repository
from src.ui.widgets.info_card import InfoCard


class Dashboard(QWidget):
    def __init__(self, repository: Repository):
        super().__init__()

        self.repository = repository
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("⚽ KreisligaManager Dashboard")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        grid = QGridLayout()

        cards = [
            ("Datenbank", "Verbunden"),
            ("Vereine", str(self.repository.count("clubs"))),
            ("Mannschaften", str(self.repository.count("teams"))),
            ("Spieler", str(self.repository.count("players"))),
            ("Spiele", str(self.repository.count("matches"))),
            ("Ereignisse", str(self.repository.count("events"))),
            ("Eventtypen", str(self.repository.count("event_types"))),
        ]

        for index, (title, value) in enumerate(cards):
            row = index // 3
            column = index % 3
            grid.addWidget(InfoCard(title, value), row, column)

        layout.addLayout(grid)
        layout.addStretch()

        self.setLayout(layout)