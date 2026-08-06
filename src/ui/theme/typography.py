from __future__ import annotations

from PySide6.QtGui import QFont


class Typography:
    """
    Zentrale Schriftdefinitionen für den KreisligaManager.
    """

    FONT_FAMILY = "Segoe UI"

    SIZE_CAPTION = 9
    SIZE_SMALL = 10
    SIZE_BODY = 11
    SIZE_SUBTITLE = 13
    SIZE_HEADING = 16
    SIZE_TITLE = 22
    SIZE_HERO = 30

    WEIGHT_NORMAL = QFont.Weight.Normal
    WEIGHT_MEDIUM = QFont.Weight.Medium
    WEIGHT_BOLD = QFont.Weight.Bold

    @classmethod
    def create(
        cls,
        size: int,
        weight: QFont.Weight = WEIGHT_NORMAL,
    ) -> QFont:
        font = QFont(cls.FONT_FAMILY)
        font.setPointSize(size)
        font.setWeight(weight)
        return font

    @classmethod
    def hero(cls) -> QFont:
        return cls.create(
            cls.SIZE_HERO,
            cls.WEIGHT_BOLD,
        )

    @classmethod
    def title(cls) -> QFont:
        return cls.create(
            cls.SIZE_TITLE,
            cls.WEIGHT_BOLD,
        )

    @classmethod
    def heading(cls) -> QFont:
        return cls.create(
            cls.SIZE_HEADING,
            cls.WEIGHT_BOLD,
        )

    @classmethod
    def subtitle(cls) -> QFont:
        return cls.create(
            cls.SIZE_SUBTITLE,
            cls.WEIGHT_MEDIUM,
        )

    @classmethod
    def body(cls) -> QFont:
        return cls.create(
            cls.SIZE_BODY,
        )

    @classmethod
    def small(cls) -> QFont:
        return cls.create(
            cls.SIZE_SMALL,
        )

    @classmethod
    def caption(cls) -> QFont:
        return cls.create(
            cls.SIZE_CAPTION,
        )