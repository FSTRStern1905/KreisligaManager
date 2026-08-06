from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QWidget,
)

from src.core.module_registry import (
    AppModule,
    ModuleRegistry,
)
from src.services.settings.module_settings_service import (
    ModuleSettings,
)


PageRefreshCallback = Callable[[QWidget], None]


class SidebarManager(QWidget):
    module_changed = Signal(str)

    MODULE_ID_ROLE = Qt.ItemDataRole.UserRole

    def __init__(
        self,
        registry: ModuleRegistry,
        settings: ModuleSettings,
        sidebar: QListWidget,
        pages: QStackedWidget,
        page_instances: dict[str, QWidget],
        refresh_callbacks: (
            dict[str, PageRefreshCallback]
            | None
        ) = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.registry = registry
        self.settings = settings
        self.sidebar = sidebar
        self.pages = pages
        self.page_instances = dict(page_instances)
        self.refresh_callbacks = dict(
            refresh_callbacks or {}
        )

        self._module_ids: list[str] = []
        self._page_indexes: dict[str, int] = {}

        self.sidebar.currentRowChanged.connect(
            self._handle_row_changed
        )

    def build(self) -> None:
        self.sidebar.blockSignals(True)

        try:
            self.sidebar.clear()
            self._clear_pages()

            self._module_ids.clear()
            self._page_indexes.clear()

            for module in self._ordered_enabled_modules():
                page = self._resolve_page(module)

                if page is None:
                    continue

                item = QListWidgetItem(
                    self._build_item_text(module)
                )
                item.setData(
                    self.MODULE_ID_ROLE,
                    module.module_id,
                )
                item.setToolTip(module.title)

                self.sidebar.addItem(item)

                page_index = self.pages.addWidget(page)

                self._module_ids.append(
                    module.module_id
                )
                self._page_indexes[
                    module.module_id
                ] = page_index

        finally:
            self.sidebar.blockSignals(False)

        self.open_start_module()

    def rebuild(
        self,
        settings: ModuleSettings | None = None,
    ) -> None:
        if settings is not None:
            self.settings = settings

        current_module_id = self.current_module_id()

        self.build()

        if (
            current_module_id
            and current_module_id
            in self._page_indexes
        ):
            self.open_module(current_module_id)

    def open_start_module(self) -> None:
        start_module = self.settings.start_module

        if start_module in self._page_indexes:
            self.open_module(start_module)
            return

        if self._module_ids:
            self.open_module(self._module_ids[0])

    def open_module(
        self,
        module_id: str,
    ) -> bool:
        normalized_id = module_id.strip()

        if normalized_id not in self._page_indexes:
            return False

        row = self._module_ids.index(normalized_id)
        self.sidebar.setCurrentRow(row)

        return True

    def current_module_id(self) -> str:
        current_item = self.sidebar.currentItem()

        if current_item is None:
            return ""

        return str(
            current_item.data(
                self.MODULE_ID_ROLE
            )
            or ""
        ).strip()

    def enabled_module_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(self._module_ids)

    def get_page(
        self,
        module_id: str,
    ) -> QWidget | None:
        return self.page_instances.get(
            module_id.strip()
        )

    def register_page(
        self,
        module_id: str,
        page: QWidget,
        refresh_callback: (
            PageRefreshCallback
            | None
        ) = None,
    ) -> None:
        normalized_id = module_id.strip()

        if not self.registry.contains(normalized_id):
            raise KeyError(
                "Modul nicht registriert: "
                f"{normalized_id}"
            )

        self.page_instances[normalized_id] = page

        if refresh_callback is not None:
            self.refresh_callbacks[
                normalized_id
            ] = refresh_callback

    def _clear_pages(self) -> None:
        while self.pages.count() > 0:
            widget = self.pages.widget(0)
            self.pages.removeWidget(widget)

    def _ordered_enabled_modules(
        self,
    ) -> tuple[AppModule, ...]:
        enabled_ids = set(
            self.settings.enabled_modules
        )

        module_by_id = {
            module.module_id: module
            for module in self.registry
        }

        ordered_modules: list[AppModule] = []

        for module_id in self.settings.module_order:
            if module_id not in enabled_ids:
                continue

            module = module_by_id.get(module_id)

            if module is not None:
                ordered_modules.append(module)

        for module in self.registry:
            if (
                module.module_id in enabled_ids
                and module not in ordered_modules
            ):
                ordered_modules.append(module)

        return tuple(ordered_modules)

    def _resolve_page(
        self,
        module: AppModule,
    ) -> QWidget | None:
        existing_page = self.page_instances.get(
            module.module_id
        )

        if existing_page is not None:
            return existing_page

        if module.page_factory is not None:
            page = module.page_factory()
            self.page_instances[
                module.module_id
            ] = page
            return page

        placeholder = self._create_placeholder(module)
        self.page_instances[
            module.module_id
        ] = placeholder

        return placeholder

    @staticmethod
    def _create_placeholder(
        module: AppModule,
    ) -> QWidget:
        label = QLabel(
            f"{module.icon} {module.title}\n\n"
            "Dieses Modul wird vorbereitet."
        )
        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        label.setObjectName(
            "ModulePlaceholder"
        )

        return label

    @staticmethod
    def _build_item_text(
        module: AppModule,
    ) -> str:
        if module.icon:
            return (
                f"{module.icon}  "
                f"{module.title}"
            )

        return module.title

    def _handle_row_changed(
        self,
        row: int,
    ) -> None:
        if (
            row < 0
            or row >= len(self._module_ids)
        ):
            return

        module_id = self._module_ids[row]
        page_index = self._page_indexes.get(
            module_id
        )

        if page_index is None:
            return

        self.pages.setCurrentIndex(page_index)

        page = self.page_instances.get(module_id)
        callback = self.refresh_callbacks.get(
            module_id
        )

        if (
            page is not None
            and callback is not None
        ):
            callback(page)

        self.module_changed.emit(module_id)