from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class InfoCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        icon: str = "",
    ):
        super().__init__()

        self.setObjectName("InfoCard")

        layout = QVBoxLayout()

        if icon:
            self.icon_label = QLabel(icon)
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setObjectName("InfoCardIcon")
            layout.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("InfoCardTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("InfoCardValue")
        self.value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

        self.setLayout(layout)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def value(self) -> str:
        return self.value_label.text()

    def set_title(self, title: str):
        self.title_label.setText(title)