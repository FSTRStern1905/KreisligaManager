from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from src.ui.theme.colors import Colors
from src.ui.theme.metrics import Metrics
from src.ui.theme.typography import Typography


class DataTable(QTableWidget):
    row_activated = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "DataTable"
        )

        self._column_keys: list[str] = []

        self._setup_table()
        self._apply_style()

        self.cellDoubleClicked.connect(
            self._handle_double_click
        )

    def _setup_table(self) -> None:
        self.setAlternatingRowColors(
            True
        )

        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.setSortingEnabled(
            True
        )

        self.setShowGrid(
            False
        )

        self.setWordWrap(
            False
        )

        self.verticalHeader().setVisible(
            False
        )

        self.verticalHeader().setDefaultSectionSize(
            Metrics.TABLE_ROW_HEIGHT
        )

        header = self.horizontalHeader()

        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        header.setMinimumSectionSize(
            80
        )

        header.setStretchLastSection(
            True
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        self.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

    def _apply_style(self) -> None:
        self.setFont(
            Typography.body()
        )

        self.setStyleSheet(
            f"""
            QTableWidget#DataTable {{
                background-color:
                    {Colors.BACKGROUND_ELEVATED};
                alternate-background-color:
                    {Colors.TABLE_ROW_ALTERNATE};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                border-radius:
                    {Metrics.RADIUS_MEDIUM}px;
                outline:
                    none;
            }}

            QTableWidget#DataTable::item {{
                color:
                    {Colors.TEXT_PRIMARY};
                padding-left:
                    {Metrics.TABLE_CELL_PADDING}px;
                padding-right:
                    {Metrics.TABLE_CELL_PADDING}px;
                border:
                    none;
            }}

            QTableWidget#DataTable::item:hover {{
                background-color:
                    {Colors.TABLE_ROW_HOVER};
                color:
                    {Colors.TEXT_PRIMARY};
            }}

            QTableWidget#DataTable::item:selected {{
                background-color:
                    {Colors.TABLE_ROW_SELECTED};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    none;
            }}

            QTableWidget#DataTable::item:selected:hover {{
                background-color:
                    {Colors.TABLE_ROW_SELECTED};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    none;
            }}

            QTableWidget#DataTable::item:selected:active {{
                background-color:
                    {Colors.TABLE_ROW_SELECTED};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    none;
            }}

            QTableWidget#DataTable::item:selected:!active {{
                background-color:
                    {Colors.TABLE_ROW_SELECTED};
                color:
                    {Colors.TEXT_PRIMARY};
                border:
                    none;
            }}

            QHeaderView::section {{
                background-color:
                    {Colors.TABLE_HEADER};
                color:
                    {Colors.TEXT_SECONDARY};
                border:
                    none;
                border-bottom:
                    {Metrics.BORDER_WIDTH}px
                    solid {Colors.BORDER};
                padding-left:
                    {Metrics.TABLE_CELL_PADDING}px;
                padding-right:
                    {Metrics.TABLE_CELL_PADDING}px;
                min-height:
                    {Metrics.TABLE_HEADER_HEIGHT}px;
            }}

            QScrollBar:vertical {{
                background:
                    transparent;
                width:
                    8px;
                margin:
                    4px 0;
            }}

            QScrollBar::handle:vertical {{
                background:
                    {Colors.SCROLLBAR_HANDLE};
                border-radius:
                    4px;
                min-height:
                    30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background:
                    {Colors.SCROLLBAR_HANDLE_HOVER};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height:
                    0;
            }}

            QScrollBar:horizontal {{
                background:
                    transparent;
                height:
                    8px;
                margin:
                    0 4px;
            }}

            QScrollBar::handle:horizontal {{
                background:
                    {Colors.SCROLLBAR_HANDLE};
                border-radius:
                    4px;
                min-width:
                    30px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background:
                    {Colors.SCROLLBAR_HANDLE_HOVER};
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width:
                    0;
            }}
            """
        )

    def set_columns(
        self,
        columns: Iterable[
            tuple[str, str]
        ],
    ) -> None:
        normalized_columns = list(
            columns
        )

        self._column_keys = [
            key
            for key, _title
            in normalized_columns
        ]

        self.setColumnCount(
            len(normalized_columns)
        )

        self.setHorizontalHeaderLabels(
            [
                title
                for _key, title
                in normalized_columns
            ]
        )

    def set_rows(
        self,
        rows: Iterable[dict],
        id_key: str = "id",
    ) -> None:
        rows_list = list(
            rows
        )

        sorting_enabled = (
            self.isSortingEnabled()
        )

        self.setSortingEnabled(
            False
        )

        self.setRowCount(
            len(rows_list)
        )

        for row_index, row_data in enumerate(
            rows_list
        ):
            row_id = row_data.get(
                id_key
            )

            for column_index, key in enumerate(
                self._column_keys
            ):
                value = row_data.get(
                    key,
                    "",
                )

                display_value = (
                    ""
                    if value is None
                    else str(value)
                )

                item = QTableWidgetItem(
                    display_value
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    row_id,
                )

                self.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.setSortingEnabled(
            sorting_enabled
        )

        self.resizeRowsToContents()

    def selected_row_id(
        self,
    ) -> int | None:
        selected_ranges = (
            self.selectedRanges()
        )

        if not selected_ranges:
            return None

        row = selected_ranges[0].topRow()

        item = self.item(
            row,
            0,
        )

        if item is None:
            return None

        value = item.data(
            Qt.ItemDataRole.UserRole
        )

        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def selected_row_data(
        self,
    ) -> dict[str, str] | None:
        selected_ranges = (
            self.selectedRanges()
        )

        if not selected_ranges:
            return None

        row = selected_ranges[0].topRow()

        result: dict[str, str] = {}

        for column_index, key in enumerate(
            self._column_keys
        ):
            item = self.item(
                row,
                column_index,
            )

            result[key] = (
                item.text()
                if item is not None
                else ""
            )

        return result

    def clear_rows(self) -> None:
        self.setRowCount(
            0
        )

    def set_column_widths(
        self,
        widths: dict[str, int],
    ) -> None:
        for key, width in widths.items():
            if key not in self._column_keys:
                continue

            column_index = (
                self._column_keys.index(
                    key
                )
            )

            self.setColumnWidth(
                column_index,
                width,
            )

    def stretch_column(
        self,
        key: str,
    ) -> None:
        if key not in self._column_keys:
            return

        column_index = (
            self._column_keys.index(
                key
            )
        )

        self.horizontalHeader().setSectionResizeMode(
            column_index,
            QHeaderView.ResizeMode.Stretch,
        )

    def _handle_double_click(
        self,
        row: int,
        _column: int,
    ) -> None:
        item = self.item(
            row,
            0,
        )

        if item is None:
            return

        row_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if row_id is None:
            return

        try:
            normalized_id = int(
                row_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return

        self.row_activated.emit(
            normalized_id
        )