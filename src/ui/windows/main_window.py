from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, QLabel
from PySide6.QtCore import Qt

from src.database.repository import Repository
from src.ui.windows.dashboard import Dashboard


class MainWindow(QMainWindow):
    def __init__(self, repository: Repository):
        super().__init__()

        self.repository = repository

        self.setWindowTitle("KreisligaManager v0.2.0-dev")
        self.resize(1100, 700)

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems([
            "Dashboard",
            "Vereine",
            "Mannschaften",
            "Spieler",
            "Spiele",
            "Import",
            "Statistiken",
            "Einstellungen",
        ])

        self.pages = QStackedWidget()
        self.dashboard = Dashboard(self.repository)

        self.pages.addWidget(self.dashboard)

        placeholder_pages = [
            "Vereine",
            "Mannschaften",
            "Spieler",
            "Spiele",
            "Import",
            "Statistiken",
            "Einstellungen",
        ]

        for page_name in placeholder_pages:
            label = QLabel(f"{page_name} kommt später")
            label.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(label)

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("Bereit")