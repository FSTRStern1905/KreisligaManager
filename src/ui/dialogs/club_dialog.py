from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
)


class ClubDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Neuer Verein")
        self.setMinimumWidth(400)

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.short_name_edit = QLineEdit()
        self.city_edit = QLineEdit()

        form.addRow("Vereinsname", self.name_edit)
        form.addRow("Kurzname", self.short_name_edit)
        form.addRow("Ort", self.city_edit)

        layout.addLayout(form)

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Speichern")
        self.cancel_button = QPushButton("Abbrechen")

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)

    def get_data(self):

        return {
            "name": self.name_edit.text(),
            "short_name": self.short_name_edit.text(),
            "city": self.city_edit.text(),
        }