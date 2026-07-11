from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CompetitionStatisticsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.competition_id = None

        self.setup_ui()
        self.connect_signals()
        self.clear_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Statistiken")
        title.setObjectName("PageTitle")

        self.info_label = QLabel(
            "Kein Wettbewerb ausgewählt"
        )
        self.info_label.setObjectName("InfoLabel")

        self.placeholder_label = QLabel(
            "Statistiken folgen in einem späteren Sprint."
        )

        self.refresh_button = QPushButton(
            "🔄 Statistiken aktualisieren"
        )
        self.refresh_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.info_label)
        layout.addWidget(self.placeholder_label)
        layout.addStretch()
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
        if self.competition_id is None:
            self.clear_data()
            return

        self.info_label.setText(
            f"Wettbewerb-ID: {self.competition_id}"
        )

        self.placeholder_label.setText(
            "Torjäger, Form, Serien und weitere Statistiken "
            "folgen in einem späteren Sprint."
        )

        self.refresh_button.setEnabled(True)

    def refresh(self):
        self.load_data()

    def clear_data(self):
        self.info_label.setText(
            "Kein Wettbewerb ausgewählt"
        )

        self.placeholder_label.setText(
            "Statistiken folgen in einem späteren Sprint."
        )

        self.refresh_button.setEnabled(False)