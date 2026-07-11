from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CompetitionTableTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Tabelle")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.table = QTableWidget()
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Mannschaft",
                "Sp",
                "S",
                "U",
                "N",
                "Tore",
                "Diff",
                "Pkt",
            ]
        )

        self.refresh_button = QPushButton(
            "🔄 Tabelle aktualisieren"
        )
        self.refresh_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.table)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def connect_signals(self):
        self.refresh_button.clicked.connect(
            self.load_data
        )

    def set_competition(
        self,
        competition_id: int | None,
    ):
        self.competition_id = competition_id

        if competition_id is None:
            self.clear_data()
            return

        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)

        if self.competition_id is None:
            self.clear_data()
            return

        self.info_label.setText(
            "Tabellenberechnung folgt im nächsten Sprint"
        )

        self.refresh_button.setEnabled(True)

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.table.setRowCount(0)

        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.refresh_button.setEnabled(False)