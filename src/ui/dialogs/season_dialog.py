from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)


class SeasonDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Neue Saison")
        self.setMinimumWidth(350)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z. B. 2026/27")

        self.start_date_input = QLineEdit()
        self.start_date_input.setPlaceholderText("z. B. 2026-08-01")

        self.end_date_input = QLineEdit()
        self.end_date_input.setPlaceholderText("z. B. 2027-05-31")

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Startdatum:", self.start_date_input)
        form_layout.addRow("Enddatum:", self.end_date_input)

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Speichern")
        self.cancel_button = QPushButton("Abbrechen")

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Eingabe fehlt",
                "Bitte gib einen Namen für die Saison ein.",
            )
            return

        if not self.start_date_input.text().strip():
            QMessageBox.warning(
                self,
                "Eingabe fehlt",
                "Bitte gib ein Startdatum ein.",
            )
            return

        if not self.end_date_input.text().strip():
            QMessageBox.warning(
                self,
                "Eingabe fehlt",
                "Bitte gib ein Enddatum ein.",
            )
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "start_date": self.start_date_input.text().strip(),
            "end_date": self.end_date_input.text().strip(),
        }