"""
Shared contract types for Kagutsuchi.

These four models are the ONLY integration surface between system/ and
verification/. See CONTRACTS.md for the field-level spec this mirrors.
Do not add/rename/remove fields without a COORDINATION.md entry.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SensitiveOp(str, Enum):
    SHELL_EXEC = "shell_exec"
    SUBPROCESS = "subprocess"
    FILESYSTEM = "filesystem"
    SQL_QUERY = "sql_query"
    DESERIALIZATION = "deserialization"
    AUTH_CHANGE = "auth_change"
    NETWORK_EGRESS = "network_egress"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExecutionPhase(str, Enum):
    BEFORE = "before"
    AFTER = "after"


class Verdict(str, Enum):
    VERIFIED_FIXED = "VERIFIED_FIXED"
    STILL_VULNERABLE = "STILL_VULNERABLE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INCONCLUSIVE = "INCONCLUSIVE"


class SecurityFinding(BaseModel):
    """Produced by system/analysis. Consumed by verification/hypothesis."""

    finding_id: str = Field(default_factory=_new_id)
    file_path: str
    symbol: str
    diff_hunk: str
    sensitive_op: SensitiveOp
    rationale: str
    detected_by: str
    severity_hint: Severity = Severity.MEDIUM


class AttackHypothesis(BaseModel):
    """Produced by verification/hypothesis. Consumed by system/sandbox."""

    hypothesis_id: str = Field(default_factory=_new_id)
    finding_id: str
    security_property: str
    attack_vector: str
    payload: str
    expected_if_vulnerable: str
    expected_if_safe: str
    generated_by: str


class ExecutionEvidence(BaseModel):
    """Produced by system/sandbox. Consumed by verification/regression."""

    evidence_id: str = Field(default_factory=_new_id)
    hypothesis_id: str
    run_id: str
    phase: ExecutionPhase
    container_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    filesystem_diff: dict = Field(default_factory=dict)
    network_egress_attempts: list = Field(default_factory=list)
    policy_violations: list = Field(default_factory=list)
    duration_ms: int = 0
    timestamp: str = Field(default_factory=_now)


class VerificationResult(BaseModel):
    """Produced by verification/regression. Consumed by system/orchestration."""

    verdict_id: str = Field(default_factory=_new_id)
    finding_id: str
    hypothesis_id: str
    before_evidence_id: str
    after_evidence_id: str
    verdict: Verdict
    replay_identical: bool
    confidence: float = 1.0
    summary: str
