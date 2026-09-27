"""
Adapters between contracts/ (system/'s types) and verification/models.py
(verification/'s independent mirror of the same contract, per
COORDINATION.md item 1 — collapsing to one source of truth is tracked
there; until then, this is the seam that keeps both sides working
together without either importing the other's package directly.

Every field name matches by construction (both were built from
contracts/CONTRACTS.md), so a JSON-mode dump-and-reconstruct is a safe,
generic conversion in both directions.
"""
from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

_T = TypeVar("_T", bound=BaseModel)


def _convert(obj: BaseModel, target_cls: type[_T]) -> _T:
    return target_cls(**obj.model_dump(mode="json"))


def to_verification(obj: BaseModel, target_cls: type[_T]) -> _T:
    """Convert a contracts/ model instance into its verification/models.py
    mirror, e.g. to_verification(finding, verification.models.SecurityFinding)."""
    return _convert(obj, target_cls)


def to_system(obj: BaseModel, target_cls: type[_T]) -> _T:
    """Convert a verification/models.py instance into its contracts/
    mirror, e.g. to_system(hypothesis, contracts.AttackHypothesis)."""
    return _convert(obj, target_cls)
