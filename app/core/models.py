"""Modelos de dados do r-check."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"


class FindingCategory(str, Enum):
    SECRET     = "secret"
    SAST       = "sast"
    DEPENDENCY = "dependency"
    IAC        = "iac"


@dataclass
class Finding:
    id: str
    title: str
    severity: Severity
    category: FindingCategory
    file_path: str
    line_number: int
    snippet: str
    description: str
    tool: list[str]
    rule_id: str = ""
    tool_notes: dict = field(default_factory=dict)  # {tool_name: descrição específica da ferramenta}
    ai_explanation: Optional[str] = None
    ai_fix_suggestion: Optional[str] = None


@dataclass
class ScanResult:
    project_path: str
    scanned_files: int
    languages_detected: list[str]
    findings: list[Finding]
    scan_duration_seconds: float
    tools_used: list[str]
    errors: list[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
