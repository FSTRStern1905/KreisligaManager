from __future__ import annotations

from src.validator.validation_result import (
    ValidationResult,
)


class PlayerValidator:
    """
    Prüft die importierten Spieler eines Spiels.
    """

    def validate(
        self,
        html_players: list,
        database_players: list,
    ) -> ValidationResult:

        result = ValidationResult(
            title="Spieler"
        )

        html_count = len(html_players)
        database_count = len(database_players)

        if html_count != database_count:
            result.add_error(
                f"Spieleranzahl unterschiedlich "
                f"(HTML={html_count}, "
                f"DB={database_count})"
            )
            return result

        html_names = {
            player.name
            for player in html_players
        }

        database_names = {
            player.name
            for player in database_players
        }

        missing = html_names - database_names
        additional = database_names - html_names

        for name in sorted(missing):
            result.add_error(
                f"Spieler fehlt: {name}"
            )

        for name in sorted(additional):
            result.add_warning(
                f"Zusätzlicher Spieler: {name}"
            )

        if (
            not result.errors
            and not result.warnings
        ):
            result.set_success()

        return result