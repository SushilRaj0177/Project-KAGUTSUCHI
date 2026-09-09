"""Pydantic mirrors of contracts/CONTRACTS.md v0.1, for verification/ only.

Do NOT edit contracts/CONTRACTS.md from here. If a field needs to change,
post a PROPOSED entry in COORDINATION.md instead (see CONTRIBUTING.md §3)
and update this file only after it's reflected there.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SensitiveOp(str, Enum):
    shell_exec = "shell_exec"
    subprocess = "subprocess"
    filesystem = "filesystem"
    sql_query = "sql_query"
    deserialization = "deserialization"
    auth_change = "auth_change"
    network_egress = "network_egress"


class SeverityHint(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class EvidencePhase(str, Enum):
    before = "before"
    after = "after"


class Verdict(str, Enum):
    VERIFIED_FIXED = "VERIFIED_FIXED"
    STILL_VULNERABLE = "STILL_VULNERABLE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INCONCLUSIVE = "INCONCLUSIVE"


class SecurityFinding(BaseModel):
    finding_id: str
    file_path: str
    symbol: str
    diff_hunk: str
    sensitive_op: SensitiveOp
    rationale: str
    detected_by: str
    severity_hint: SeverityHint


class AttackHypothesis(BaseModel):
    hypothesis_id: str
    finding_id: str
    security_property: str
    attack_vector: str
    payload: str
    expected_if_vulnerable: str
    expected_if_safe: str
    generated_by: str


class ExecutionEvidence(BaseModel):
    evidence_id: str
    hypothesis_id: str
    run_id: str
    phase: EvidencePhase
    container_id: str
    exit_code: int
    stdout: str
    stderr: str
    filesystem_diff: dict[str, Any] = Field(default_factory=dict)
    network_egress_attempts: list[Any] = Field(default_factory=list)
    policy_violations: list[Any] = Field(default_factory=list)
    duration_ms: int
    timestamp: str


class VerificationResult(BaseModel):
    verdict_id: str
    finding_id: str
    hypothesis_id: str
    before_evidence_id: str
    after_evidence_id: str
    verdict: Verdict
    replay_identical: bool
    confidence: float
    summary: str
