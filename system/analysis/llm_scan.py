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

Beyond per-file findings, this ALSO asks the model to propose a brand-new
deterministic detector (a DetectorProposal) when it spots a vulnerability
pattern outside the fixed sensitive_op categories — the mechanism for
"the AI catches what's not listed, and the deterministic list keeps
growing" (see COORDINATION.md's detector-proposal workflow). A proposal
is NEVER auto-merged into ast_scan.py's _SIGNATURES: letting live,
LLM-derived output silently rewrite the trusted static-analysis code
path would be a real self-modifying-code risk (a crafted repo could try
to trick the model into proposing a bogus or overly broad signature).
Proposals are surfaced for human/session review and manually promoted
via scripts/promote_detector.py, same review discipline the project
already applies to hand-authored signature proposals.

On any failure (no API key, network, malformed JSON) this returns empty
results rather than raising - it's an additive layer on top of ast_scan,
so a Groq outage degrades detection breadth, not the whole scan.
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts import SecurityFinding, Severity, SensitiveOp
from verification.hypothesis.groq_client import DEFAULT_MODEL, GroqUnavailable, generate_hypothesis_json

_VALID_OPS = {op.value for op in SensitiveOp}
_VALID_SEVERITIES = {sev.value for sev in Severity}

# Cap how much source we hand the model per file - keeps prompts (and
# cost/latency) bounded for large files without truncating mid-function
# for anything reasonably sized.
_MAX_SOURCE_CHARS = 12_000

# Told to the model so it doesn't waste its one proposal slot re-suggesting
# a class ast_scan.py already detects. Kept as a plain literal list rather
# than importing ast_scan.py's _SIGNATURES dict at runtime: this is
# deliberately a hint for prompt quality, not a correctness dependency -
# scan_source_with_llm must keep working even if ast_scan.py's internals
# are refactored, and a stale hint here just means an occasional redundant
# proposal, not a bug.
_KNOWN_DETECTOR_SIGNATURES = (
    "os.system, subprocess.run, subprocess.Popen, subprocess.call, eval, exec, "
    "pickle.loads, os.popen, marshal.loads, os.execv, os.execve, os.spawnv, "
    "raw SQL string building, Django .raw()/.extra(), yaml.load with an unsafe "
    "loader, Jinja2/render_template_string SSTI"
)

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

Respond with a single JSON object with two top-level keys: "findings" and \
"new_class_proposal".

"findings" must be a list. Each element is an object with exactly these keys:
  symbol          - the function name the vulnerability is in
  diff_hunk       - the exact vulnerable code snippet (the relevant lines, \
copied verbatim from the source above - not paraphrased)
  sensitive_op    - the single best-fitting tag from this exact list: \
shell_exec, subprocess, filesystem, sql_query, deserialization, auth_change, \
network_egress, other
  rationale       - one or two sentences on why this is exploitable
  severity_hint   - one of: low, medium, high

If you find nothing genuinely exploitable, "findings" must be [] - do not \
invent a vulnerability just to have something to report.

"new_class_proposal": a fixed-signature static analyzer (matching exact \
function/method call names, not reasoning about meaning) already catches: \
{known_signatures}. If this file contains a genuinely different \
exploitable pattern that such a literal-call-name matcher could ALSO learn \
to catch - i.e. the dangerous part is a specific, nameable function/method \
call, not something that requires understanding context - propose it as an \
object with exactly these keys:
  class_name      - a short snake_case identifier for this vulnerability \
class, e.g. "server_side_request_forgery"
  call_signature  - the EXACT dotted call name a static analyzer should \
match, e.g. "requests.get" or "xml.etree.ElementTree.parse" - concrete \
enough to add as a literal signature, not a vague description
  rationale       - why matching this call name is a meaningful, generally \
exploitable signal, not specific to just this one file
  severity_hint   - one of: low, medium, high
If nothing qualifies (either nothing new, or the pattern genuinely needs \
judgment a literal signature match can't provide), set "new_class_proposal" \
to null. Only propose something you'd stand behind as a real, reusable \
detector - not a one-off guess.
"""


@dataclass
class DetectorProposal:
    """A candidate NEW entry for ast_scan.py's deterministic _SIGNATURES
    table, discovered by the LLM scan finding a vulnerability pattern
    outside the fixed category list. Never auto-applied - see this
    module's docstring."""

    class_name: str
    call_signature: str
    rationale: str
    severity_hint: str
    source_file_path: str


@dataclass
class LlmScanResult:
    findings: list[SecurityFinding]
    proposal: DetectorProposal | None


def _parse_findings(raw_findings: object, file_path: str, model: str) -> list[SecurityFinding]:
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


def _parse_proposal(raw_proposal: object, file_path: str) -> DetectorProposal | None:
    if not isinstance(raw_proposal, dict):
        return None
    class_name = raw_proposal.get("class_name")
    call_signature = raw_proposal.get("call_signature")
    rationale = raw_proposal.get("rationale")
    severity = raw_proposal.get("severity_hint")
    if not all(isinstance(v, str) and v for v in (class_name, call_signature, rationale)):
        return None
    return DetectorProposal(
        class_name=class_name,
        call_signature=call_signature,
        rationale=rationale,
        severity_hint=severity if severity in _VALID_SEVERITIES else "medium",
        source_file_path=file_path,
    )


def scan_source_with_llm(source: str, file_path: str, model: str = DEFAULT_MODEL) -> LlmScanResult:
    """Ask an LLM to find vulnerabilities in `source` beyond ast_scan's
    fixed pattern list, and to propose a new deterministic detector if it
    spots a pattern that a literal call-name match could also catch.
    Never raises - returns an empty result on any failure."""
    prompt = _PROMPT_TEMPLATE.format(
        file_path=file_path,
        source=source[:_MAX_SOURCE_CHARS],
        known_signatures=_KNOWN_DETECTOR_SIGNATURES,
    )
    try:
        raw = generate_hypothesis_json(prompt, model=model)
    except GroqUnavailable:
        return LlmScanResult(findings=[], proposal=None)

    if not isinstance(raw, dict):
        return LlmScanResult(findings=[], proposal=None)

    findings = _parse_findings(raw.get("findings"), file_path, model)
    proposal = _parse_proposal(raw.get("new_class_proposal"), file_path)
    return LlmScanResult(findings=findings, proposal=proposal)
