"""
LLM-based candidate-finding pass, run alongside (not instead of)
ast_scan.py's pattern matching.

ast_scan.py only recognizes a fixed list of call signatures — it is
structurally blind to any vulnerability class nobody hand-coded a rule
for (SSRF, IDOR, hardcoded secrets, weak crypto, template injection
outside the one pattern coded for it, ...) and to non-trivial data flow
even inside the classes it does know. An LLM reading the whole function
for *meaning* rather than matching a call name can catch what the rule
list can't.

The safety property that makes this acceptable: nothing here is trusted
because it came back well-formed. Every finding this produces becomes an
ordinary SecurityFinding and flows into the EXACT same downstream
pipeline as an ast_scan finding — hypothesize -> real sandboxed attack ->
verify. If the LLM's hunch is wrong, the attack simply fails to create
the marker file and it comes back FALSE_POSITIVE, same as a wrong
AST-based finding would. The LLM proposes; the sandbox disposes. It never
gets to declare something vulnerable on its own say-so.

On any failure (no API key, network, malformed JSON) this returns an
empty list rather than raising - it's an additive layer on top of
ast_scan, so a Groq outage degrades detection breadth, not the whole
scan.
"""
from __future__ import annotations

from contracts import SecurityFinding, Severity, SensitiveOp
from verification.hypothesis.groq_client import DEFAULT_MODEL, GroqUnavailable, generate_hypothesis_json

_VALID_OPS = {op.value for op in SensitiveOp}
_VALID_SEVERITIES = {sev.value for sev in Severity}

# Cap how much source we hand the model per file - keeps prompts (and
# cost/latency) bounded for large files without truncating mid-function
# for anything reasonably sized.
_MAX_SOURCE_CHARS = 12_000

_PROMPT_TEMPLATE = """You are a security auditor reviewing a Python file for \
REAL, exploitable vulnerabilities - not style issues, not theoretical concerns. \
Find every distinct vulnerability you can, of ANY class: command injection, SQL \
injection, insecure deserialization, path traversal, SSRF, IDOR/broken access \
control, hardcoded secrets/credentials, weak or misused cryptography, template \
injection (SSTI), unsafe use of eval/exec, authentication/authorization bypass, \
XXE, or anything else genuinely exploitable. Ignore purely stylistic or \
best-practice nits that aren't actually exploitable.

file_path: {file_path}

source:
{source}

Respond with a single JSON object: {{"findings": [...]}}. Each element of \
`findings` must be an object with exactly these keys:
  symbol          - the function name the vulnerability is in
  diff_hunk       - the exact vulnerable code snippet (the relevant lines, \
copied verbatim from the source above - not paraphrased)
  sensitive_op    - the single best-fitting tag from this exact list: \
shell_exec, subprocess, filesystem, sql_query, deserialization, auth_change, \
network_egress, other
  rationale       - one or two sentences on why this is exploitable
  severity_hint   - one of: low, medium, high

If you find nothing genuinely exploitable, respond with {{"findings": []}}. \
Do not invent a vulnerability just to have something to report.
"""


def scan_source_with_llm(
    source: str, file_path: str, model: str = DEFAULT_MODEL
) -> list[SecurityFinding]:
    """Ask an LLM to find vulnerabilities in `source` beyond ast_scan's
    fixed pattern list. Never raises - returns [] on any failure."""
    prompt = _PROMPT_TEMPLATE.format(file_path=file_path, source=source[:_MAX_SOURCE_CHARS])
    try:
        raw = generate_hypothesis_json(prompt, model=model)
    except GroqUnavailable:
        return []

    raw_findings = raw.get("findings") if isinstance(raw, dict) else None
    if not isinstance(raw_findings, list):
        return []

    findings: list[SecurityFinding] = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        op = item.get("sensitive_op")
        severity = item.get("severity_hint")
        symbol = item.get("symbol")
        diff_hunk = item.get("diff_hunk")
        rationale = item.get("rationale")
        if op not in _VALID_OPS or not all(isinstance(v, str) and v for v in (symbol, diff_hunk, rationale)):
            continue  # malformed entry from the model - skip it, don't crash the scan
        findings.append(
            SecurityFinding(
                file_path=file_path,
                symbol=symbol,
                diff_hunk=diff_hunk,
                sensitive_op=SensitiveOp(op),
                rationale=rationale,
                detected_by=f"llm:{model}",
                severity_hint=Severity(severity) if severity in _VALID_SEVERITIES else Severity.MEDIUM,
            )
        )
    return findings
