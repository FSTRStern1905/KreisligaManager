from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
)


class LeagueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Neue Liga")
        self.setMinimumWidth(350)

        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z. B. Kreisliga A")

        self.level_spin = QSpinBox()
        self.level_spin.setMinimum(1)
        self.level_spin.setMaximum(20)
        self.level_spin.setValue(8)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Ebene:", self.level_spin)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "level": self.level_spin.value(),
        }