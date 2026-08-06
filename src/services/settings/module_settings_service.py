from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.module_registry import (
    ModuleRegistry,
)


@dataclass(slots=True)
class ModuleSettings:
    enabled_modules: list[str] = field(
        default_factory=list
    )
    module_order: list[str] = field(
        default_factory=list
    )
    start_module: str = "dashboard"

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled_modules": list(
                self.enabled_modules
            ),
            "module_order": list(
                self.module_order
            ),
            "start_module": self.start_module,
        }


class ModuleSettingsService:
    DEFAULT_PATH = Path(
        "config/user_settings.json"
    )

    def __init__(
        self,
        registry: ModuleRegistry,
        path: str | Path | None = None,
    ) -> None:
        self.registry = registry
        self.path = Path(
            path
            if path is not None
            else self.DEFAULT_PATH
        )

    def load(
        self,
    ) -> ModuleSettings:
        if not self.path.exists():
            settings = self.create_default_settings()
            self.save(
                settings
            )
            return settings

        try:
            raw_data = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            json.JSONDecodeError,
            OSError,
        ):
            settings = self.create_default_settings()
            self.save(
                settings
            )
            return settings

        if not isinstance(
            raw_data,
            dict,
        ):
            settings = self.create_default_settings()
            self.save(
                settings
            )
            return settings

        settings = ModuleSettings(
            enabled_modules=self._normalize_module_ids(
                raw_data.get(
                    "enabled_modules",
                    [],
                )
            ),
            module_order=self._normalize_module_ids(
                raw_data.get(
                    "module_order",
                    [],
                )
            ),
            start_module=str(
                raw_data.get(
                    "start_module",
                    "dashboard",
                )
                or "dashboard"
            ).strip(),
        )

        settings = self.validate(
            settings
        )

        self.save(
            settings
        )

        return settings

    def save(
        self,
        settings: ModuleSettings,
    ) -> None:
        validated = self.validate(
            settings
        )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.write_text(
            json.dumps(
                validated.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def create_default_settings(
        self,
    ) -> ModuleSettings:
        enabled_modules = [
            module.module_id
            for module
            in self.registry.enabled_by_default()
        ]

        module_order = [
            module.module_id
            for module
            in self.registry.all_modules()
        ]

        return ModuleSettings(
            enabled_modules=enabled_modules,
            module_order=module_order,
            start_module="dashboard",
        )

    def validate(
        self,
        settings: ModuleSettings,
    ) -> ModuleSettings:
        known_ids = {
            module.module_id
            for module in self.registry
        }

        required_ids = {
            module.module_id
            for module in self.registry
            if module.required
        }

        enabled_modules = [
            module_id
            for module_id
            in self._unique(
                settings.enabled_modules
            )
            if module_id in known_ids
        ]

        for module_id in required_ids:
            if module_id not in enabled_modules:
                enabled_modules.append(
                    module_id
                )

        module_order = [
            module_id
            for module_id
            in self._unique(
                settings.module_order
            )
            if module_id in known_ids
        ]

        for module in self.registry.all_modules():
            if module.module_id not in module_order:
                module_order.append(
                    module.module_id
                )

        start_module = settings.start_module.strip()

        if (
            start_module not in known_ids
            or start_module not in enabled_modules
        ):
            start_module = (
                "dashboard"
                if "dashboard" in enabled_modules
                else enabled_modules[0]
            )

        return ModuleSettings(
            enabled_modules=enabled_modules,
            module_order=module_order,
            start_module=start_module,
        )

    def is_enabled(
        self,
        settings: ModuleSettings,
        module_id: str,
    ) -> bool:
        return (
            module_id.strip()
            in settings.enabled_modules
        )

    def set_enabled(
        self,
        settings: ModuleSettings,
        module_id: str,
        enabled: bool,
    ) -> ModuleSettings:
        module = self.registry.get(
            module_id
        )

        enabled_modules = list(
            settings.enabled_modules
        )

        if module.required:
            enabled = True

        if enabled:
            if module.module_id not in enabled_modules:
                enabled_modules.append(
                    module.module_id
                )
        else:
            enabled_modules = [
                current_id
                for current_id
                in enabled_modules
                if current_id != module.module_id
            ]

        updated = ModuleSettings(
            enabled_modules=enabled_modules,
            module_order=list(
                settings.module_order
            ),
            start_module=settings.start_module,
        )

        return self.validate(
            updated
        )

    def set_start_module(
        self,
        settings: ModuleSettings,
        module_id: str,
    ) -> ModuleSettings:
        normalized_id = module_id.strip()

        if not self.registry.contains(
            normalized_id
        ):
            raise KeyError(
                "Unbekanntes Startmodul: "
                f"{normalized_id}"
            )

        if normalized_id not in settings.enabled_modules:
            raise ValueError(
                "Das Startmodul muss aktiviert sein: "
                f"{normalized_id}"
            )

        updated = ModuleSettings(
            enabled_modules=list(
                settings.enabled_modules
            ),
            module_order=list(
                settings.module_order
            ),
            start_module=normalized_id,
        )

        return self.validate(
            updated
        )

    def move_module(
        self,
        settings: ModuleSettings,
        module_id: str,
        new_index: int,
    ) -> ModuleSettings:
        normalized_id = module_id.strip()

        if not self.registry.contains(
            normalized_id
        ):
            raise KeyError(
                "Unbekanntes Modul: "
                f"{normalized_id}"
            )

        order = [
            current_id
            for current_id
            in settings.module_order
            if current_id != normalized_id
        ]

        bounded_index = max(
            0,
            min(
                new_index,
                len(order),
            ),
        )

        order.insert(
            bounded_index,
            normalized_id,
        )

        updated = ModuleSettings(
            enabled_modules=list(
                settings.enabled_modules
            ),
            module_order=order,
            start_module=settings.start_module,
        )

        return self.validate(
            updated
        )

    @staticmethod
    def _normalize_module_ids(
        value: Any,
    ) -> list[str]:
        if not isinstance(
            value,
            list,
        ):
            return []

        return [
            str(module_id).strip()
            for module_id in value
            if str(module_id).strip()
        ]

    @staticmethod
    def _unique(
        values: list[str],
    ) -> list[str]:
        return list(
            dict.fromkeys(
                values
            )
        )