from __future__ import annotations

from src.services.validation.validation_result import (
    ValidationCheck,
    ValidationResult,
)


class ValidationReport:
    STATUS_PASS = "PASS"
    STATUS_INFO = "INFO"
    STATUS_WARNING = "WARNING"
    STATUS_ERROR = "ERROR"

    def build_text(
        self,
        result: ValidationResult,
    ) -> str:
        lines = [
            "=" * 60,
            "IMPORT-VALIDIERUNG",
            "=" * 60,
            "",
        ]

        if result.total_checks == 0:
            lines.extend(
                [
                    "Keine Prüfungen durchgeführt.",
                    "",
                    "=" * 60,
                ]
            )

            return "\n".join(
                lines
            )

        for check in result.checks:
            lines.extend(
                self._format_check(
                    check
                )
            )

        lines.extend(
            [
                "=" * 60,
                "ZUSAMMENFASSUNG",
                "=" * 60,
                "",
                (
                    "PASS:                     "
                    f"{result.passed_checks}"
                ),
                (
                    "INFO:                     "
                    f"{result.info_checks}"
                ),
                (
                    "WARNUNG:                  "
                    f"{result.warning_checks}"
                ),
                (
                    "FEHLER:                   "
                    f"{result.failed_checks}"
                ),
                (
                    "Prüfungen insgesamt:      "
                    f"{result.total_checks}"
                ),
                (
                    "Reine Erfolgsquote:        "
                    f"{result.success_rate:.1f} %"
                ),
                (
                    "Gewichtete Datenqualität:  "
                    f"{result.quality_rate:.1f} %"
                ),
                (
                    "Einzelinfos:               "
                    f"{result.info_count}"
                ),
                (
                    "Einzelwarnungen:           "
                    f"{result.warning_count}"
                ),
                (
                    "Einzelfehler:              "
                    f"{result.error_count}"
                ),
                "",
                self._build_overall_status(
                    result
                ),
                "",
                "=" * 60,
            ]
        )

        return "\n".join(
            lines
        )

    def build_compact_text(
        self,
        result: ValidationResult,
    ) -> str:
        if result.total_checks == 0:
            return (
                "Validierung: Keine Prüfungen "
                "durchgeführt."
            )

        return (
            "Validierung: "
            f"{result.passed_checks} PASS"
            f" | {result.info_checks} INFO"
            f" | {result.warning_checks} WARNUNG"
            f" | {result.failed_checks} FEHLER"
            f" | Qualität "
            f"{result.quality_rate:.1f} %"
        )

    def build_dict(
        self,
        result: ValidationResult,
    ) -> dict:
        return {
            "passed_checks": (
                result.passed_checks
            ),
            "info_checks": (
                result.info_checks
            ),
            "warning_checks": (
                result.warning_checks
            ),
            "failed_checks": (
                result.failed_checks
            ),
            "total_checks": (
                result.total_checks
            ),
            "success_rate": round(
                result.success_rate,
                1,
            ),
            "quality_rate": round(
                result.quality_rate,
                1,
            ),
            "info_count": (
                result.info_count
            ),
            "warning_count": (
                result.warning_count
            ),
            "error_count": (
                result.error_count
            ),
            "is_valid": (
                result.is_valid
            ),
            "checks": [
                self._check_to_dict(
                    check
                )
                for check in result.checks
            ],
        }

    def _format_check(
        self,
        check: ValidationCheck,
    ) -> list[str]:
        symbol = self._get_symbol(
            check.status
        )

        lines = [
            f"{symbol} {check.name}",
        ]

        for info in check.infos:
            lines.append(
                f"    ℹ {info}"
            )

        for warning in check.warnings:
            lines.append(
                f"    ⚠ {warning}"
            )

        for error in check.errors:
            lines.append(
                f"    ✖ {error}"
            )

        if (
            not check.infos
            and not check.warnings
            and not check.errors
        ):
            lines.append(
                "    Keine Auffälligkeiten."
            )

        lines.append(
            ""
        )

        return lines

    @staticmethod
    def _build_overall_status(
        result: ValidationResult,
    ) -> str:
        if result.has_errors:
            return (
                "ERGEBNIS: FEHLER GEFUNDEN"
            )

        if result.has_warnings:
            return (
                "ERGEBNIS: MIT WARNUNGEN "
                "ABGESCHLOSSEN"
            )

        if result.has_infos:
            return (
                "ERGEBNIS: MIT HINWEISEN "
                "ABGESCHLOSSEN"
            )

        return (
            "ERGEBNIS: ALLE PRÜFUNGEN "
            "ERFOLGREICH"
        )

    @staticmethod
    def _get_symbol(
        status: str,
    ) -> str:
        if status == ValidationReport.STATUS_PASS:
            return "✔"

        if status == ValidationReport.STATUS_INFO:
            return "ℹ"

        if status == ValidationReport.STATUS_WARNING:
            return "⚠"

        return "✖"

    @staticmethod
    def _check_to_dict(
        check: ValidationCheck,
    ) -> dict:
        return {
            "name": check.name,
            "passed": check.passed,
            "status": check.status,
            "infos": list(
                check.infos
            ),
            "warnings": list(
                check.warnings
            ),
            "errors": list(
                check.errors
            ),
        }