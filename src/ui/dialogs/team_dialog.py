from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class TeamDialog(QDialog):

    def __init__(self, clubs, parent=None):
        super().__init__(parent)

        self.clubs = clubs

        self.setWindowTitle("Neue Mannschaft")
        self.setMinimumWidth(400)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.club_box = QComboBox()

        for club_id, name in self.clubs:
            self.club_box.addItem(name, club_id)

        self.team_number = QSpinBox()
        self.team_number.setRange(1, 20)
        self.team_number.setValue(1)

        self.short_name = QComboBox()
        self.short_name.addItems(
            [
                "I",
                "II",
                "III",
                "IV",
                "U19",
                "U17",
                "U15",
                "AH",
                "Frauen",
            ]
        )

        form.addRow("Verein:", self.club_box)
        form.addRow("Mannschaft:", self.short_name)
        form.addRow("Nummer:", self.team_number)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Speichern")
        self.cancel_button = QPushButton("Abbrechen")

        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def connect_signals(self):
        self.save_button.clicked.connect(self.validate)
        self.cancel_button.clicked.connect(self.reject)

    def validate(self):
        if self.club_box.currentIndex() < 0:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte einen Verein auswählen.",
            )
            return

        self.accept()

    def get_data(self):
        return {
            "club_id": self.club_box.currentData(),
            "team_name": self.short_name.currentText(),
            "team_number": self.team_number.value(),
        }