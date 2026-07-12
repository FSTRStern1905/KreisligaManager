from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class MatchDialog(QDialog):
    STATUS_OPTIONS = [
        ("Geplant", "scheduled"),
        ("Live", "live"),
        ("Beendet", "finished"),
        ("Verlegt", "postponed"),
        ("Abgesagt", "cancelled"),
        ("Abgebrochen", "abandoned"),
    ]

    def __init__(
        self,
        match_data: dict,
        stadiums: list[tuple],
        referees: list[tuple],
        parent=None,
    ):
        super().__init__(parent)

        self.match_data = match_data
        self.stadiums = stadiums
        self.referees = referees

        self.setWindowTitle("Spiel bearbeiten")
        self.resize(560, 560)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel(
            f"{self.match_data['home_team']}  vs  "
            f"{self.match_data['away_team']}"
        )
        title.setObjectName("PageTitle")

        form = QFormLayout()

        self.home_goals = QSpinBox()
        self.home_goals.setRange(0, 99)

        self.away_goals = QSpinBox()
        self.away_goals.setRange(0, 99)

        self.status_box = QComboBox()

        for label, value in self.STATUS_OPTIONS:
            self.status_box.addItem(label, value)

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("z. B. 2026-08-09")

        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("z. B. 15:00")

        self.stadium_box = QComboBox()
        self.stadium_box.addItem("Kein Stadion", None)

        for stadium_id, stadium_name in self.stadiums:
            self.stadium_box.addItem(
                stadium_name,
                stadium_id,
            )

        self.referee_box = QComboBox()
        self.referee_box.addItem("Kein Schiedsrichter", None)

        for referee_id, referee_name in self.referees:
            self.referee_box.addItem(
                referee_name,
                referee_id,
            )

        self.attendance = QSpinBox()
        self.attendance.setRange(0, 100000)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText(
            "Notizen zum Spiel..."
        )
        self.notes_edit.setMinimumHeight(100)

        form.addRow("Heimtore:", self.home_goals)
        form.addRow("Auswärtstore:", self.away_goals)
        form.addRow("Status:", self.status_box)
        form.addRow("Datum:", self.date_edit)
        form.addRow("Anstoß:", self.time_edit)
        form.addRow("Stadion:", self.stadium_box)
        form.addRow("Schiedsrichter:", self.referee_box)
        form.addRow("Zuschauer:", self.attendance)
        form.addRow("Notizen:", self.notes_edit)

        buttons = QHBoxLayout()

        save_button = QPushButton("💾 Speichern")
        cancel_button = QPushButton("Abbrechen")

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        buttons.addStretch()
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)

        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def load_data(self):
        self.home_goals.setValue(
            self.match_data["home_goals"]
            if self.match_data["home_goals"] is not None
            else 0
        )

        self.away_goals.setValue(
            self.match_data["away_goals"]
            if self.match_data["away_goals"] is not None
            else 0
        )

        self.date_edit.setText(
            self.match_data["date"] or ""
        )

        self.time_edit.setText(
            self.match_data["time"] or ""
        )

        self.attendance.setValue(
            self.match_data["attendance"] or 0
        )

        self.notes_edit.setPlainText(
            self.match_data["notes"] or ""
        )

        status_index = self.status_box.findData(
            self.match_data["status"]
        )

        if status_index >= 0:
            self.status_box.setCurrentIndex(status_index)

        stadium_index = self.stadium_box.findData(
            self.match_data["stadium_id"]
        )

        if stadium_index >= 0:
            self.stadium_box.setCurrentIndex(stadium_index)

        referee_index = self.referee_box.findData(
            self.match_data["referee_id"]
        )

        if referee_index >= 0:
            self.referee_box.setCurrentIndex(referee_index)

    def get_data(self):
        return {
            "home_goals": self.home_goals.value(),
            "away_goals": self.away_goals.value(),
            "status": self.status_box.currentData(),
            "date": self.date_edit.text().strip(),
            "time": self.time_edit.text().strip(),
            "stadium_id": self.stadium_box.currentData(),
            "referee_id": self.referee_box.currentData(),
            "attendance": self.attendance.value(),
            "notes": self.notes_edit.toPlainText().strip(),
        }