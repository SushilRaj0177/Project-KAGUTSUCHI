"""
M4a: AST-based static detection of sensitive-operation call sites -
re-platformed from `engine-archive/kagutsuchi/system/analysis/ast_scan.py`
onto the wsqfai domain model, not reinvented from scratch. The detection
logic (signature table, taint-propagation gate, SQL/YAML/SSTI heuristics)
is carried over close to verbatim, since it was already exercised against
real code in production Kagutsuchi; what changes here is what it produces.

This is deliberately scoped as *hypothesis generation only*. The original
Kagutsuchi engine named its output "SecurityFinding" and fed it into a
sandbox that actually attempted the exploit before anything was reported
as proven - see `engine-archive/kagutsuchi/verification/`. That
proven-not-asserted discipline is the single most load-bearing security
decision in ARCHITECTURE.md's design-decision trace, so a static AST match
alone must NOT mint a wsqfai `Finding` (a Finding is a claim that a
sub-characteristic is *at risk*, backed by evidence of that risk - not
backed by evidence of a mere pattern match). Every hit here becomes an
`Observation` instead: "this call site matches a sensitive-operation
signature", not "this is a vulnerability". Promoting an Observation to a
Finding is the sandbox-verification stage - wsqfai/security/verify.py
(M4b), re-platforming `engine-archive/kagutsuchi/system/sandbox`. It
currently covers a handful of mechanically reconstructible shapes (a
direct shell-exec/eval/exec call whose tainted data reaches the sink
directly from one of its own parameters - the function can take other
parameters too now, as long as exactly one of them is the one that call
actually uses; see verify.py's own docstring); every other Observation
stays a hypothesis until that coverage widens further.

Parses Python source, walks each function body, and flags calls that match
a known sensitive-operation signature (shell exec, subprocess, filesystem,
SQL, deserialization, ...). It is intentionally a signature match over the
AST, not a general taint/dataflow analysis, with one deliberate exception
(see `_tainted_names`/`_call_is_tainted`): a dangerous call is only
reported if at least one of its arguments could possibly carry data
derived from the enclosing function's own parameters - without that gate,
a call like `subprocess.run(["rm", "-rf", TMP_DIR])` in some unrelated
maintenance script would be flagged purely because it calls a dangerous
function, true by name but not a real signal.

Two pieces of the archived original are deliberately left out of this
first port rather than carried over unused: `scan_diff`/`changed_functions`
(diff-scoped scanning, so only functions touched by a change are reported)
and `LearnedSignature`/`extra_signatures` (human-approved detector
proposals fed back into the scan). Both depended on machinery (a
CI diff view, a review/approval workflow) that hasn't been re-platformed
yet - reintroducing them without that machinery would just be dead
parameters. Real M4b/M6 work, not forgotten.
"""
from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from enum import Enum

from wsqfai.domain.evidence import Observation, Severity, SourceLocation

_MAX_RETAINED_SNIPPET_CHARS = 2000


class SensitiveOp(str, Enum):
    SHELL_EXEC = "shell_exec"
    SUBPROCESS = "subprocess"
    FILESYSTEM = "filesystem"
    SQL_QUERY = "sql_query"
    DESERIALIZATION = "deserialization"
    AUTH_CHANGE = "auth_change"
    NETWORK_EGRESS = "network_egress"


# Which Security sub_characteristic (wsqfai.domain.quality_model) a proven
# instance of this op would put at risk - carried as metadata now, for
# whichever Finding M4b eventually mints once sandbox-verified. A single
# best-fit key per op, not an exhaustive mapping: SQL injection, say, can
# also threaten confidentiality, but integrity (unauthorized modification
# of data/control flow) is the more universally applicable claim across
# every op in this table.
_LIKELY_SUB_CHARACTERISTIC: dict[SensitiveOp, str] = {
    SensitiveOp.SHELL_EXEC: "integrity",
    SensitiveOp.SUBPROCESS: "integrity",
    SensitiveOp.DESERIALIZATION: "integrity",
    SensitiveOp.SQL_QUERY: "integrity",
    SensitiveOp.AUTH_CHANGE: "authenticity",
    SensitiveOp.FILESYSTEM: "integrity",
    SensitiveOp.NETWORK_EGRESS: "confidentiality",
}

_SEVERITY_BY_OP: dict[SensitiveOp, Severity] = {
    SensitiveOp.SHELL_EXEC: Severity.HIGH,
    SensitiveOp.SUBPROCESS: Severity.HIGH,
    SensitiveOp.DESERIALIZATION: Severity.HIGH,
    SensitiveOp.SQL_QUERY: Severity.HIGH,
    SensitiveOp.AUTH_CHANGE: Severity.HIGH,
    SensitiveOp.FILESYSTEM: Severity.MEDIUM,
    SensitiveOp.NETWORK_EGRESS: Severity.MEDIUM,
}

# Qualified call name -> (SensitiveOp, rationale, detector id)
_SIGNATURES: dict[str, tuple[SensitiveOp, str, str]] = {
    "os.system": (
        SensitiveOp.SHELL_EXEC,
        "os.system runs its argument through the shell — string-built "
        "input here is a classic command injection sink.",
        "ast.shell_exec.os_system",
    ),
    "subprocess.run": (
        SensitiveOp.SUBPROCESS,
        "subprocess.run can invoke a shell (shell=True) or pass an "
        "attacker-influenced argv.",
        "ast.subprocess.run",
    ),
    "subprocess.Popen": (
        SensitiveOp.SUBPROCESS,
        "subprocess.Popen can invoke a shell (shell=True) or pass an "
        "attacker-influenced argv.",
        "ast.subprocess.popen",
    ),
    "subprocess.call": (
        SensitiveOp.SUBPROCESS,
        "subprocess.call can invoke a shell (shell=True) or pass an "
        "attacker-influenced argv.",
        "ast.subprocess.call",
    ),
    "eval": (
        SensitiveOp.DESERIALIZATION,
        "eval executes arbitrary Python from its argument.",
        "ast.eval",
    ),
    "exec": (
        SensitiveOp.DESERIALIZATION,
        "exec executes arbitrary Python from its argument.",
        "ast.exec",
    ),
    "pickle.loads": (
        SensitiveOp.DESERIALIZATION,
        "pickle.loads can execute arbitrary code during unpickling of "
        "untrusted data.",
        "ast.pickle.loads",
    ),
    "os.popen": (
        SensitiveOp.SHELL_EXEC,
        "os.popen runs its argument through the shell.",
        "ast.shell_exec.os_popen",
    ),
    "marshal.loads": (
        SensitiveOp.DESERIALIZATION,
        "marshal.loads can execute/reconstruct arbitrary code objects "
        "from untrusted data, the same class of risk as pickle.loads.",
        "ast.marshal.loads",
    ),
    "os.execv": (
        SensitiveOp.SUBPROCESS,
        "os.execv replaces the current process image with an "
        "attacker-influenced argv.",
        "ast.subprocess.os_execv",
    ),
    "os.execve": (
        SensitiveOp.SUBPROCESS,
        "os.execve replaces the current process image with an "
        "attacker-influenced argv/environment.",
        "ast.subprocess.os_execve",
    ),
    "os.spawnv": (
        SensitiveOp.SUBPROCESS,
        "os.spawnv spawns a new process with an attacker-influenced argv.",
        "ast.subprocess.os_spawnv",
    ),
}


@dataclass
class _CallSite:
    function_name: str
    call_name: str
    lineno: int
    op: SensitiveOp | None = None
    rationale: str | None = None
    detector: str | None = None
    severity: Severity | None = None
    shell_true: bool = False
    direct_taint_param: str | None = None
    other_params_json: str | None = None


def _is_string_built(node: ast.expr) -> bool:
    """True if `node` looks like a runtime-assembled string: an f-string,
    or string concatenation (`"..." + var`), rather than a plain literal."""
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return True
    return False


def _sql_call_hit(node: ast.Call) -> _CallSite | None:
    """Heuristic: cursor.execute(...)/.executescript(...) where the query
    argument is string-built, not a parameterized literal — the actual
    SQL-injection-relevant pattern, independent of the cursor's module."""
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in ("execute", "executescript"):
        return None
    if not node.args or not _is_string_built(node.args[0]):
        return None
    return _CallSite(
        function_name="",
        call_name=f"<obj>.{func.attr}",
        lineno=node.lineno,
        op=SensitiveOp.SQL_QUERY,
        rationale=(
            f".{func.attr} is called with a string built at runtime "
            "(f-string/concatenation) instead of a parameterized query — "
            "classic SQL injection sink."
        ),
        detector="ast.sql_injection.string_built_query",
    )


def _django_sql_call_hit(node: ast.Call) -> _CallSite | None:
    """Extends _sql_call_hit to Django ORM's .raw()/.extra(where=...) —
    same string-built-argument heuristic, different method names."""
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr == "raw":
        if not node.args or not _is_string_built(node.args[0]):
            return None
        return _CallSite(
            function_name="",
            call_name="<queryset>.raw",
            lineno=node.lineno,
            op=SensitiveOp.SQL_QUERY,
            rationale=(
                ".raw() is called with a string built at runtime — Django's "
                "raw SQL escape hatch bypasses ORM parameterization."
            ),
            detector="ast.sql_injection.django_raw",
        )
    if func.attr == "extra":
        where_arg = next((kw.value for kw in node.keywords if kw.arg == "where"), None)
        if where_arg is None or not (
            isinstance(where_arg, (ast.List, ast.Tuple))
            and any(_is_string_built(elt) for elt in where_arg.elts)
        ):
            return None
        return _CallSite(
            function_name="",
            call_name="<queryset>.extra",
            lineno=node.lineno,
            op=SensitiveOp.SQL_QUERY,
            rationale=(
                ".extra(where=[...]) with a string built at runtime injects "
                "raw SQL into the WHERE clause, bypassing parameterization."
            ),
            detector="ast.sql_injection.django_extra",
        )
    return None


def _yaml_load_hit(node: ast.Call) -> _CallSite | None:
    """yaml.load(data, Loader=X) is safe only if X names a Safe loader.
    yaml.load(data) with no Loader kwarg at all is also flagged - older
    PyYAML defaults to the unsafe Loader in that case."""
    if _dotted_call_name(node) != "yaml.load":
        return None
    loader_kw = next((kw.value for kw in node.keywords if kw.arg == "Loader"), None)
    if loader_kw is not None:
        loader_name = None
        if isinstance(loader_kw, ast.Attribute):
            loader_name = loader_kw.attr
        elif isinstance(loader_kw, ast.Name):
            loader_name = loader_kw.id
        elif isinstance(loader_kw, ast.Call):
            loader_name = _dotted_call_name(loader_kw)
        if loader_name and "Safe" in loader_name:
            return None
    return _CallSite(
        function_name="",
        call_name="yaml.load",
        lineno=node.lineno,
        op=SensitiveOp.DESERIALIZATION,
        rationale=(
            "yaml.load() without Loader=yaml.SafeLoader can construct "
            "arbitrary Python objects from untrusted YAML, a known "
            "code-execution sink (use yaml.safe_load instead)."
        ),
        detector="ast.deserialization.yaml_load_unsafe",
    )


def _ssti_hit(node: ast.Call) -> _CallSite | None:
    """flask.render_template_string(x) or a Jinja2 Template(x).render(...)
    where the template source itself is string-built - server-side
    template injection, a code-execution sink."""
    name = _dotted_call_name(node)
    if name in ("render_template_string", "flask.render_template_string"):
        if node.args and _is_string_built(node.args[0]):
            return _CallSite(
                function_name="",
                call_name=name,
                lineno=node.lineno,
                op=SensitiveOp.DESERIALIZATION,
                rationale=(
                    "render_template_string compiles and executes its "
                    "argument as a Jinja2 template - string-built input "
                    "is server-side template injection (SSTI)."
                ),
                detector="ast.ssti.render_template_string",
            )
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "render" and isinstance(func.value, ast.Call):
        inner_name = _dotted_call_name(func.value)
        if inner_name in ("Template", "jinja2.Template") and func.value.args and _is_string_built(func.value.args[0]):
            return _CallSite(
                function_name="",
                call_name="Template(...).render",
                lineno=node.lineno,
                op=SensitiveOp.DESERIALIZATION,
                rationale=(
                    "jinja2.Template() is constructed from a string built "
                    "at runtime, then rendered - server-side template "
                    "injection (SSTI), a code-execution sink."
                ),
                detector="ast.ssti.jinja2_template",
            )
    return None


_SHELL_TRUE_CALLS = {"subprocess.run", "subprocess.Popen", "subprocess.call"}


def _call_has_shell_true(node: ast.Call) -> bool:
    """True if this call passes an explicit `shell=True` keyword. Only
    meaningful for subprocess.run/Popen/call: with `shell=True`, the
    command argument is handed to a real shell, which is exactly what
    makes a generic shell-metacharacter payload work regardless of the
    function's own base command - the same property `os.system`/
    `os.popen` have unconditionally. Without this keyword, subprocess.*
    execs argv directly with no shell involved at all, so the same
    payload would do nothing - which is why M4b's verification only
    attempts these calls when this is true (see verify.py)."""
    for kw in node.keywords:
        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _dotted_call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        cur: ast.expr = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
    return None


def _param_names(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = func_node.args
    names = {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)
    return names


def _expr_references(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node))


def _tainted_names(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names that could carry data from this function's own parameters into
    a dangerous call: seeded with the parameters themselves, then propagated
    one hop at a time through plain `x = <expr>` assignments whose
    right-hand side already references a tainted name (e.g. `raw =
    base64.b64decode(data)` taints `raw` because `data` is a parameter).

    This is a small fixed-point over a handful of statements, not a real
    dataflow analysis - it exists only to answer "could an argument to this
    call possibly be attacker-influenced at all", so that a dangerous call
    built entirely from hardcoded/literal arguments (a maintenance script's
    `subprocess.run(["rm", "-rf", TMP_DIR])`, say) isn't reported as if it
    were an injection sink just because the function happens to take some
    unrelated parameter.
    """
    tainted = _param_names(func_node)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(func_node):
            target_name = None
            value = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target_name, value = node.targets[0].id, node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                target_name, value = node.target.id, node.value
            if target_name is not None and target_name not in tainted and _expr_references(value, tainted):
                tainted.add(target_name)
                changed = True
    return tainted


def _call_is_tainted(node: ast.Call, tainted: set[str]) -> bool:
    """Whether this call could carry data derived from the enclosing
    function's own parameters - the gate that keeps a dangerous call made
    only with hardcoded/literal arguments from being flagged as if
    attacker input could reach it."""
    return _expr_references(node, tainted)


def _callable_positional_params(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str] | None:
    """Ordered positional-or-keyword parameter names, when the function's
    signature is simple enough that M4b's verifier can safely reconstruct
    a call for it purely with keyword arguments (see
    `_direct_taint_param_for_call` and `verify.build_candidate_script`) -
    order then never matters, so there's no risk of a positional
    mismatch. None for anything this slice doesn't attempt: positional-only
    params (can't be passed by keyword at all), *args, or **kwargs (no
    static way to know what a caller would put there)."""
    args = func_node.args
    if args.posonlyargs or args.vararg or args.kwarg or args.kwonlyargs:
        return None
    return [a.arg for a in args.args]


def _positional_defaults(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, ast.expr]:
    """Map parameter name -> its default value expression, for the plain
    positional-or-keyword parameters `_callable_positional_params` returns.
    `ast.arguments.defaults` aligns to the *trailing* parameters, the same
    way Python itself resolves defaults, so a 2-default function's list
    lines up against its last two parameter names, not its first two."""
    args = func_node.args
    names = [a.arg for a in args.args]
    defaults = args.defaults
    if not defaults:
        return {}
    offset = len(names) - len(defaults)
    return {names[offset + i]: default for i, default in enumerate(defaults)}


def _direct_taint_param_for_call(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef, call_node: ast.Call, tainted: set[str]
) -> str | None:
    """The one function parameter whose data reaches `call_node` directly -
    by name, with no intermediate local variable - among a signature this
    slice can safely reconstruct a call for at all (see
    `_callable_positional_params`). Generalizes what used to require the
    function have exactly one parameter total: a function can now take
    several parameters, as long as exactly one of them is the one this
    particular call actually uses.

    Returns None for anything ambiguous or indirect, the same discipline
    the single-parameter case always had:
      - the taint reaching this call only via a derived local - an
        intermediate variable (`raw = data; pickle.loads(raw)`), or the
        receiver of a method call derived from a parameter
        (`cursor = conn.cursor(); cursor.execute(...)` - `cursor` is
        itself untainted-by-name but derived from `conn`, so reconstructing
        a bare `cursor.execute(...)` call site-less isn't possible anyway);
      - more than one parameter referenced directly in the call itself
        (`os.system(f"ping -c {count} {host}")` with both `count` and
        `host` as parameters) - which one would a verifier inject the
        payload into?
    A false negative here (a real but unreconstructed shape) is an honest,
    stated limitation; this function never returns a parameter name unless
    the call for it really can be built unambiguously."""
    param_names = _callable_positional_params(func_node)
    if param_names is None:
        return None
    param_set = set(param_names)
    derived_tainted = tainted - param_set
    if derived_tainted and _expr_references(call_node, derived_tainted):
        return None
    referenced_params = {p for p in param_set if _expr_references(call_node, {p})}
    if len(referenced_params) != 1:
        return None
    return next(iter(referenced_params))


def _other_params_metadata(func_node: ast.FunctionDef | ast.AsyncFunctionDef, taint_param: str) -> str | None:
    """JSON-encoded `[[name, default_source_or_null], ...]` for every
    callable parameter other than `taint_param` - what M4b's verifier
    (`wsqfai/security/verify.py`) needs to fill in the rest of a real
    function's arity so the candidate call doesn't fail with a plain
    `TypeError: missing required argument` before the sink is ever reached.
    `default_source` is the parameter's own default expression, reproduced
    verbatim via `ast.unparse` when the function declares one; `null` when
    it doesn't; a metadata dict is flat `dict[str, str]`, hence the JSON
    encoding rather than a nested structure. None (not just `"[]"`) when
    there are no other parameters, so the wire shape for the single-
    parameter case this slice originally supported is completely
    unchanged."""
    other_params = [p for p in (_callable_positional_params(func_node) or []) if p != taint_param]
    if not other_params:
        return None
    defaults = _positional_defaults(func_node)
    return json.dumps([[p, ast.unparse(defaults[p]) if p in defaults else None] for p in other_params])


def sensitive_ops_in_function(func_node: ast.FunctionDef) -> list[_CallSite]:
    hits: list[_CallSite] = []
    tainted = _tainted_names(func_node)
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        if not _call_is_tainted(node, tainted):
            continue
        direct_taint_param = _direct_taint_param_for_call(func_node, node, tainted)
        other_params_json = _other_params_metadata(func_node, direct_taint_param) if direct_taint_param else None
        name = _dotted_call_name(node)
        if name in _SIGNATURES:
            shell_true = name in _SHELL_TRUE_CALLS and _call_has_shell_true(node)
            hits.append(_CallSite(
                func_node.name, name, node.lineno, shell_true=shell_true,
                direct_taint_param=direct_taint_param, other_params_json=other_params_json,
            ))
            continue
        for heuristic in (_sql_call_hit, _django_sql_call_hit, _yaml_load_hit, _ssti_hit):
            hit = heuristic(node)
            if hit is not None:
                hit.function_name = func_node.name
                hit.direct_taint_param = direct_taint_param
                hit.other_params_json = other_params_json
                hits.append(hit)
                break
    return hits


def _function_source(source_lines: list[str], func_node: ast.FunctionDef) -> str:
    end = getattr(func_node, "end_lineno", func_node.lineno)
    text = "\n".join(source_lines[func_node.lineno - 1 : end])
    return text[:_MAX_RETAINED_SNIPPET_CHARS]


def _module_level_imports(tree: ast.Module) -> str:
    """Reconstructed source text of every top-level import statement in
    the file. A function's own body frequently relies on a name (`os`,
    `subprocess`, ...) imported at module scope rather than inside the
    function itself - the common real-world case, as opposed to the
    import-inside-the-function style some hand-written fixtures use.
    Without these, a candidate script built from `_function_source` alone
    fails with a bare NameError before the sink is ever reached, which
    M4b's verification (wsqfai/security/verify.py) would otherwise
    misread as "not vulnerable" rather than "couldn't even run"."""
    lines = [
        ast.unparse(node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    return "\n".join(lines)[:_MAX_RETAINED_SNIPPET_CHARS]


def scan_source(source: str, file_path: str) -> list[Observation]:
    """Parse `source`, return one Observation per sensitive call site found
    inside any top-level or nested function definition. Returns an empty
    list, rather than raising, if `source` doesn't parse as valid Python -
    a scanner that crashes the whole run on one malformed file is worse
    than one that skips it."""
    try:
        tree = ast.parse(source, filename=file_path)
    except (SyntaxError, ValueError):
        return []
    source_lines = source.splitlines()
    module_imports = _module_level_imports(tree)
    observations: list[Observation] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for hit in sensitive_ops_in_function(node):  # type: ignore[arg-type]
            op, rationale, detector = hit.op, hit.rationale, hit.detector
            if op is None:
                op, rationale, detector = _SIGNATURES[hit.call_name]
            severity = hit.severity or _SEVERITY_BY_OP.get(op, Severity.MEDIUM)
            metadata = {
                "sensitive_op": op.value,
                "detected_by": detector,
                "severity_hint": severity.value,
                "symbol": hit.function_name,
                "likely_security_sub_characteristic": _LIKELY_SUB_CHARACTERISTIC[op],
                "function_source": _function_source(source_lines, node),
            }
            if module_imports:
                metadata["module_imports"] = module_imports
            if hit.shell_true:
                metadata["shell_true"] = "true"
            if hit.direct_taint_param is not None:
                metadata["single_param_direct_taint"] = hit.direct_taint_param
                if hit.other_params_json is not None:
                    metadata["other_params"] = hit.other_params_json
            observations.append(Observation(
                description=f"{rationale} (call: {hit.call_name}, line {hit.lineno})",
                location=SourceLocation(file_path=file_path, start_line=hit.lineno, end_line=hit.lineno),
                metadata=metadata,
            ))
    return observations
