from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationIssue:
    category: str
    message: str


@dataclass(slots=True)
class ValidationResult:
    checks: int = 0
    passed: int = 0
    failed: int = 0

    issues: list[ValidationIssue] = field(default_factory=list)

    def success(self) -> None:
        self.checks += 1
        self.passed += 1

    def error(self, category: str, message: str) -> None:
        self.checks += 1
        self.failed += 1
        self.issues.append(
            ValidationIssue(
                category=category,
                message=message,
            )
        )

    @property
    def score(self) -> float:
        if self.checks == 0:
            return 100.0

        return (self.passed / self.checks) * 100

    def print_report(self) -> None:

        print()
        print("=" * 60)
        print("VALIDIERUNGSBERICHT")
        print("=" * 60)

        print(f"Prüfungen : {self.checks}")
        print(f"Bestanden : {self.passed}")
        print(f"Fehler    : {self.failed}")
        print(f"Score     : {self.score:.1f}%")

        if not self.issues:
            print()
            print("Keine Abweichungen gefunden.")
            return

        print()
        print("Abweichungen:")

        for issue in self.issues:
            print(f"[{issue.category}] {issue.message}")