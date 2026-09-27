"""
The repository-level entry point for M4a: run `ast_scan.scan_source` over
every Python file in a RepositorySnapshot that has retained content, and
collect the resulting Observations. Kept as its own tiny module, separate
from ast_scan.py's per-file detection logic, because the sandbox
verification stage (M4b) will need a comparable repository-level entry
point of its own that takes these Observations as input - keeping "scan
one file" and "scan a repository" as separate functions now makes that
composition straightforward later.
"""
from __future__ import annotations

from wsqfai.domain.evidence import Observation
from wsqfai.ingestion.repository import RepositorySnapshot
from wsqfai.security.ast_scan import scan_source


def scan_repository_for_security_hypotheses(snapshot: RepositorySnapshot) -> list[Observation]:
    """Real, unverified security hypotheses - see ast_scan.py's module
    docstring for why these are Observations, not Findings, until a
    sandbox-verification stage (M4b) proves one actually exploitable."""
    observations: list[Observation] = []
    for f in snapshot.files:
        if f.language != "Python" or not f.content:
            continue
        observations.extend(scan_source(f.content, f.path))
    return observations
