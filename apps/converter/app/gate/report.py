"""What the gate answers: one result per check G1 ... G12, the journeys, and the first failure by name."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["passed", "failed", "not_applicable"]


@dataclass(frozen=True)
class Finding:
    path: str       # JSON pointer inside the form ("" when the finding is about the form as a whole)
    message: str


@dataclass
class CheckResult:
    id: str
    name: str
    status: Status = "passed"
    findings: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)   # reported, never failing
    reason: str = ""                                         # why not_applicable
    detail: dict[str, Any] = field(default_factory=dict)     # counts, for the sidecar and the review page


@dataclass
class JourneyResult:
    id: str
    name: str
    status: Status
    reason: str = ""
    findings: list[Finding] = field(default_factory=list)
    visible: list[str] = field(default_factory=list)          # techNames shown on this journey, sorted


class GateFailed(Exception):
    """Raised by GateReport.raise_for_failure(): the service answers 500 GATE_FAILED with the check, never the form."""

    def __init__(self, check: CheckResult) -> None:
        self.check = check
        first = check.findings[0] if check.findings else Finding("", "")
        super().__init__(f"{check.id} {check.name}: {first.message} at {first.path or '/'}")


@dataclass
class GateReport:
    profile: str
    checks: list[CheckResult]
    journeys: list[JourneyResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(c.status == "failed" for c in self.checks)

    @property
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "failed"]

    def get(self, check_id: str) -> CheckResult:
        return next(c for c in self.checks if c.id == check_id)

    def raise_for_failure(self) -> None:
        if self.failed:
            raise GateFailed(self.failed[0])

    def to_dict(self) -> dict[str, Any]:
        return {"profile": self.profile, "passed": self.passed,
                "checks": [asdict(c) for c in self.checks], "journeys": [asdict(j) for j in self.journeys]}
