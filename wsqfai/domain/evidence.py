"""
The canonical Finding / Evidence / Observation model - the single most
important architectural discipline in WSQF-AI, deliberately separated the
way Project KAGUTSUCHI's own Evidence Engine separated them (and the way
this project's CodeSentinel-era planning called out as essential before
any AI/scoring/dashboard layer is trustworthy):

  Observation  - something noticed about the repository. Not necessarily a
                 problem (e.g. "this file has no type hints").
  Evidence     - the concrete, repository-relative proof behind a claim
                 (file, line, code snippet, analyzer + rule that produced
                 it). Traceable back to an exact place in the repository.
  Finding      - a claim that a QualitySubCharacteristic (see
                 quality_model.py) is at risk, backed by one or more
                 Evidence items.
  AIAssessment - what an AI layer concluded after reading the Evidence.
                 Never itself a source of truth - it explains, prioritizes,
                 or correlates; it does not get to invent a Finding with no
                 Evidence behind it.

This mirrors ISO/IEC 25000-2 (SQuaRE Vocabulary)'s own discipline of
distinguishing a quality model's characteristics from the measures used to
evaluate them - Findings attach to a named QualitySubCharacteristic, never
a free-text "category" string.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(str, Enum):
    """How sure the producing analyzer is - distinct from an AI's own
    stated confidence (AIAssessment.confidence below), which can differ."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SourceLocation(BaseModel):
    """A repository-relative pointer - never an absolute filesystem path,
    since those are meaningless outside the one clone that produced them
    and would silently break evidence provenance the moment a repo is
    re-cloned into a different temp directory."""

    file_path: str
    start_line: int | None = None
    end_line: int | None = None

    @field_validator("file_path")
    @classmethod
    def _no_absolute_paths(cls, v: str) -> str:
        if v.startswith("/") or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"SourceLocation.file_path must be repository-relative, got absolute path: {v!r}")
        return v


class AnalyzerMetadata(BaseModel):
    """Which analyzer produced this evidence, and how sure it is - kept
    separate from the Evidence's actual content so a Finding can honestly
    show its full provenance chain: repo -> file/line -> analyzer -> rule
    -> observed evidence -> (optionally) AI interpretation."""

    analyzer: str
    rule_id: str | None = None
    confidence: Confidence = Confidence.MEDIUM


class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=_new_id)
    location: SourceLocation
    snippet: str
    analyzer: AnalyzerMetadata
    created_at: str = Field(default_factory=_now)


class Observation(BaseModel):
    """Something noticed about the repository that is NOT itself a claim of
    risk - e.g. "uses framework X", "42% of functions have no type hints".
    Findings may cite Observations as supporting context, but an
    Observation alone never becomes a Finding without an analyzer actually
    asserting risk against a QualitySubCharacteristic."""

    observation_id: str = Field(default_factory=_new_id)
    description: str
    location: SourceLocation | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AIAssessment(BaseModel):
    """What an AI layer concluded after reading a Finding's Evidence.
    Explicitly NOT where a Finding's existence originates - see this
    module's docstring. A Finding is valid with zero AIAssessments; an
    AIAssessment never exists without a Finding it's assessing."""

    model: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: str = Field(default_factory=_now)


class Finding(BaseModel):
    """A claim that a named QualitySubCharacteristic (quality_model.py) is
    at risk in this repository, backed by at least one Evidence item.
    Mirrors ISO/IEC 25000-2's discipline: a Finding names the standard's
    own vocabulary, not an ad hoc category invented by whichever detector
    produced it."""

    finding_id: str = Field(default_factory=_new_id)
    title: str
    description: str
    characteristic: QualityCharacteristic
    sub_characteristic_key: str
    severity: Severity
    evidence: list[Evidence] = Field(min_length=1)
    related_observations: list[Observation] = Field(default_factory=list)
    ai_assessment: AIAssessment | None = None
    created_at: str = Field(default_factory=_now)

    @field_validator("sub_characteristic_key")
    @classmethod
    def _sub_characteristic_must_exist(cls, v: str) -> str:
        try:
            sub_characteristic(v)
        except KeyError:
            raise ValueError(f"unknown sub_characteristic_key: {v!r}") from None
        return v

    @field_validator("sub_characteristic_key")
    @classmethod
    def _sub_characteristic_must_belong_to_characteristic(cls, v: str, info) -> str:
        characteristic = info.data.get("characteristic")
        if characteristic is not None and sub_characteristic(v).characteristic != characteristic:
            raise ValueError(
                f"sub_characteristic {v!r} belongs to {sub_characteristic(v).characteristic}, "
                f"not the declared characteristic {characteristic}"
            )
        return v
