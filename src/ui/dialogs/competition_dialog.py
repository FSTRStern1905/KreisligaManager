from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class CompetitionDialog(QDialog):
    def __init__(self, leagues, seasons, parent=None):
        super().__init__(parent)

        self.leagues = leagues
        self.seasons = seasons

        self.setWindowTitle("Neuer Wettbewerb")
        self.setMinimumWidth(420)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            "z. B. Kreisliga A 2026/27"
        )

        self.league_box = QComboBox()

        for league in self.leagues:
            self.league_box.addItem(
                league.display_name,
                league.league_id,
            )

        self.season_box = QComboBox()

        for season_id, season_name in self.seasons:
            self.season_box.addItem(
                season_name,
                season_id,
            )

        self.active_checkbox = QCheckBox("Aktiv")
        self.active_checkbox.setChecked(True)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Liga:", self.league_box)
        form_layout.addRow("Saison:", self.season_box)
        form_layout.addRow("", self.active_checkbox)

        layout.addLayout(form_layout)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def connect_signals(self):
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(
                self,
                "Eingabe fehlt",
                "Bitte gib einen Namen für den Wettbewerb ein.",
            )
            return

        if self.league_box.currentIndex() < 0:
            QMessageBox.warning(
                self,
                "Liga fehlt",
                "Bitte wähle eine Liga aus.",
            )
            return

        if self.season_box.currentIndex() < 0:
            QMessageBox.warning(
                self,
                "Saison fehlt",
                "Bitte wähle eine Saison aus.",
            )
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "league_id": self.league_box.currentData(),
            "season_id": self.season_box.currentData(),
            "active": self.active_checkbox.isChecked(),
        }