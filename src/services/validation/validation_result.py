from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationCheck:
    name: str
    passed: bool
    infos: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )
    errors: list[str] = field(
        default_factory=list
    )

    @property
    def status(self) -> str:
        if self.errors:
            return "ERROR"

        if self.warnings:
            return "WARNING"

        if self.infos:
            return "INFO"

        if self.passed:
            return "PASS"

        return "ERROR"

    @property
    def is_pass(self) -> bool:
        return self.status == "PASS"

    @property
    def is_info(self) -> bool:
        return self.status == "INFO"

    @property
    def is_warning(self) -> bool:
        return self.status == "WARNING"

    @property
    def is_error(self) -> bool:
        return self.status == "ERROR"


@dataclass(slots=True)
class ValidationResult:
    checks: list[ValidationCheck] = field(
        default_factory=list
    )

    def add_check(
        self,
        check: ValidationCheck,
    ) -> None:
        self.checks.append(
            check
        )

    @property
    def passed_checks(self) -> int:
        return sum(
            check.is_pass
            for check in self.checks
        )

    @property
    def info_checks(self) -> int:
        return sum(
            check.is_info
            for check in self.checks
        )

    @property
    def warning_checks(self) -> int:
        return sum(
            check.is_warning
            for check in self.checks
        )

    @property
    def failed_checks(self) -> int:
        return sum(
            check.is_error
            for check in self.checks
        )

    @property
    def total_checks(self) -> int:
        return len(
            self.checks
        )

    @property
    def info_count(self) -> int:
        return sum(
            len(check.infos)
            for check in self.checks
        )

    @property
    def warning_count(self) -> int:
        return sum(
            len(check.warnings)
            for check in self.checks
        )

    @property
    def error_count(self) -> int:
        return sum(
            len(check.errors)
            for check in self.checks
        )

    @property
    def success_rate(self) -> float:
        if not self.checks:
            return 100.0

        return (
            self.passed_checks
            / self.total_checks
            * 100
        )

    @property
    def quality_rate(self) -> float:
        if not self.checks:
            return 100.0

        weighted_score = (
            self.passed_checks * 1.0
            + self.info_checks * 0.9
            + self.warning_checks * 0.6
        )

        return (
            weighted_score
            / self.total_checks
            * 100
        )

    @property
    def has_infos(self) -> bool:
        return self.info_checks > 0

    @property
    def has_warnings(self) -> bool:
        return self.warning_checks > 0

    @property
    def has_errors(self) -> bool:
        return self.failed_checks > 0

    @property
    def is_valid(self) -> bool:
        return not self.has_errors