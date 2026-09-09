"""
AST-based structural analysis.

Parses Python source, walks each function body, and flags calls that match
a known sensitive-operation signature (shell exec, subprocess, filesystem,
SQL, deserialization, ...). Each match becomes a SecurityFinding — the
system/ side's only output, consumed by verification/hypothesis.

This is intentionally a signature match over the AST, not a taint/dataflow
analysis: P0 scope is proving ONE demonstrated vulnerability class end to
end, not building a general static analyzer.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from contracts import SecurityFinding, SensitiveOp, Severity

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


def sensitive_ops_in_function(func_node: ast.FunctionDef) -> list[_CallSite]:
    hits: list[_CallSite] = []
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted_call_name(node)
        if name in _SIGNATURES:
            hits.append(_CallSite(func_node.name, name, node.lineno))
            continue
        for heuristic in (_sql_call_hit, _django_sql_call_hit, _yaml_load_hit, _ssti_hit):
            hit = heuristic(node)
            if hit is not None:
                hit.function_name = func_node.name
                hits.append(hit)
                break
    return hits


def _function_source(source_lines: list[str], func_node: ast.FunctionDef) -> str:
    end = getattr(func_node, "end_lineno", func_node.lineno)
    return "\n".join(source_lines[func_node.lineno - 1 : end])


def scan_source(
    source: str, file_path: str, *, only_symbols: set[str] | None = None
) -> list[SecurityFinding]:
    """Parse `source`, return one SecurityFinding per sensitive call site
    found inside any top-level or nested function definition.

    If `only_symbols` is given, restrict findings to functions whose name
    is in that set — used by scan_diff to report only on changed code.
    """
    tree = ast.parse(source, filename=file_path)
    source_lines = source.splitlines()
    findings: list[SecurityFinding] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if only_symbols is not None and node.name not in only_symbols:
                continue
            for hit in sensitive_ops_in_function(node):  # type: ignore[arg-type]
                if hit.op is not None:
                    op, rationale, detector = hit.op, hit.rationale, hit.detector
                else:
                    op, rationale, detector = _SIGNATURES[hit.call_name]
                findings.append(
                    SecurityFinding(
                        file_path=file_path,
                        symbol=hit.function_name,
                        diff_hunk=_function_source(source_lines, node),
                        sensitive_op=op,
                        rationale=f"{rationale} (call: {hit.call_name}, line {hit.lineno})",
                        detected_by=detector,
                        severity_hint=_SEVERITY_BY_OP.get(op, Severity.MEDIUM),
                    )
                )
    return findings


def _function_sources(source: str) -> dict[str, str]:
    """Map function name -> its exact source text, for diffing against
    another version of the same file."""
    tree = ast.parse(source)
    lines = source.splitlines()
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = _function_source(lines, node)
    return out


def changed_functions(old_source: str, new_source: str) -> set[str]:
    """Names of functions that are new in `new_source` or whose body text
    differs from `old_source` — a lightweight stand-in for a real git-diff
    hunk mapping, sufficient for isolating the changed function per commit."""
    old_funcs = _function_sources(old_source)
    new_funcs = _function_sources(new_source)
    return {
        name
        for name, body in new_funcs.items()
        if name not in old_funcs or old_funcs[name] != body
    }


def scan_diff(old_source: str, new_source: str, file_path: str) -> list[SecurityFinding]:
    """The actual "detect" entry point: only report sensitive ops inside
    functions that changed between `old_source` and `new_source`, not the
    whole file — this is what keeps a finding scoped to the change under
    review instead of re-flagging pre-existing code on every commit."""
    changed = changed_functions(old_source, new_source)
    return scan_source(new_source, file_path, only_symbols=changed)
