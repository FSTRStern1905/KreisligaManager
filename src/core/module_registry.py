from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget


PageFactory = Callable[[], QWidget]


@dataclass(slots=True)
class AppModule:
    module_id: str
    title: str
    icon: str
    category: str
    order: int
    enabled_by_default: bool = True
    required: bool = False
    page_factory: PageFactory | None = None

    def __post_init__(self) -> None:
        self.module_id = self.module_id.strip()
        self.title = self.title.strip()
        self.icon = self.icon.strip()
        self.category = self.category.strip()

        if not self.module_id:
            raise ValueError(
                "module_id darf nicht leer sein."
            )

        if not self.title:
            raise ValueError(
                "title darf nicht leer sein."
            )

        if self.order < 0:
            raise ValueError(
                "order darf nicht negativ sein."
            )


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, AppModule] = {}

    def register(
        self,
        module: AppModule,
    ) -> None:
        if module.module_id in self._modules:
            raise ValueError(
                "Modul bereits registriert: "
                f"{module.module_id}"
            )

        self._modules[module.module_id] = module

    def unregister(
        self,
        module_id: str,
    ) -> None:
        normalized_id = module_id.strip()

        if normalized_id not in self._modules:
            raise KeyError(
                "Modul nicht registriert: "
                f"{normalized_id}"
            )

        del self._modules[normalized_id]

    def get(
        self,
        module_id: str,
    ) -> AppModule:
        normalized_id = module_id.strip()

        if normalized_id not in self._modules:
            raise KeyError(
                "Modul nicht gefunden: "
                f"{normalized_id}"
            )

        return self._modules[normalized_id]

    def contains(
        self,
        module_id: str,
    ) -> bool:
        return module_id.strip() in self._modules

    def all_modules(
        self,
    ) -> tuple[AppModule, ...]:
        return tuple(
            sorted(
                self._modules.values(),
                key=lambda module: (
                    module.category.casefold(),
                    module.order,
                    module.title.casefold(),
                ),
            )
        )

    def enabled_by_default(
        self,
    ) -> tuple[AppModule, ...]:
        return tuple(
            module
            for module in self.all_modules()
            if (
                module.enabled_by_default
                or module.required
            )
        )

    def categories(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                module.category
                for module in self.all_modules()
            )
        )

    def modules_by_category(
        self,
        category: str,
    ) -> tuple[AppModule, ...]:
        normalized_category = (
            category.strip().casefold()
        )

        return tuple(
            module
            for module in self.all_modules()
            if (
                module.category.casefold()
                == normalized_category
            )
        )

    def clear(
        self,
    ) -> None:
        self._modules.clear()

    def __len__(
        self,
    ) -> int:
        return len(self._modules)

    def __iter__(self):
        return iter(self.all_modules())


def create_default_registry() -> ModuleRegistry:
    registry = ModuleRegistry()

    modules = (
        AppModule(
            "dashboard",
            "Dashboard",
            "🏠",
            "Übersicht",
            10,
            True,
            True,
        ),
        AppModule(
            "calendar",
            "Kalender",
            "📅",
            "Übersicht",
            20,
        ),
        AppModule(
            "clubs",
            "Vereine",
            "🏟",
            "Verwaltung",
            10,
        ),
        AppModule(
            "seasons",
            "Saisons",
            "🗓",
            "Verwaltung",
            20,
        ),
        AppModule(
            "teams",
            "Mannschaften",
            "👥",
            "Verwaltung",
            30,
        ),
        AppModule(
            "players",
            "Spieler",
            "👤",
            "Verwaltung",
            40,
        ),
        AppModule(
            "competitions",
            "Wettbewerbe",
            "🏆",
            "Fußball",
            10,
        ),
        AppModule(
            "matches",
            "Spiele",
            "⚽",
            "Fußball",
            20,
        ),
        AppModule(
            "statistics",
            "Statistiken",
            "📊",
            "Fußball",
            30,
        ),
        AppModule(
            "import",
            "Import",
            "📥",
            "System",
            10,
        ),
        AppModule(
            "settings",
            "Einstellungen",
            "⚙",
            "System",
            20,
            True,
            True,
        ),
        AppModule(
            "groundhopping",
            "Groundhopping",
            "🗺",
            "Erweiterungen",
            10,
            False,
        ),
        AppModule(
            "photography",
            "Fotografenmodus",
            "📸",
            "Erweiterungen",
            20,
            False,
        ),
        AppModule(
            "training",
            "Training",
            "🏋",
            "Erweiterungen",
            30,
            False,
        ),
        AppModule(
            "simulation",
            "Simulation",
            "🎲",
            "Erweiterungen",
            40,
            False,
        ),
    )

    for module in modules:
        registry.register(module)

    return registry