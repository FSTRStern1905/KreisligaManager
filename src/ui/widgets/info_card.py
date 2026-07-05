from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class InfoCard(QFrame):
    def __init__(self, title: str, value: str):
        super().__init__()

        self.setObjectName("InfoCard")

        title_label = QLabel(title)
        title_label.setObjectName("InfoCardTitle")

        value_label = QLabel(value)
        value_label.setObjectName("InfoCardValue")

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(value_label)

        self.setLayout(layout)