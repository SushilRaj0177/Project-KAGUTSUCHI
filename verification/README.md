# verification/

This is the "prove it, don't claim it" half of Kagutsuchi. Given a
`SecurityFinding` (a flagged line of code from `system/analysis`), this
package generates one concrete attack, and — once `system/sandbox` has
actually run that attack before and after a fix — scores the result into
a `VerificationResult`. It never runs untrusted code itself (that's
`system/sandbox`'s job, in a Docker container) and it never asks an LLM
whether a fix "looks safe" (that's `regression/verify.py`'s job, from
hard evidence). Its only contract with the rest of the system is the four
types in [`contracts/CONTRACTS.md`](../contracts/CONTRACTS.md).

If you're a judge skimming this repo: the three fixtures under
`fixtures/` are real, runnable, exploitable Python — not pseudocode — and
every verdict in this README was produced by an actual Docker container
running actual code, not asserted.

## The three fixtures

Each fixture is a pair of functions, `vulnerable()` and `fixed()`, each
taking one attacker-controlled string. The same fixture module is handed
to `system/orchestration/harness.py`'s `build_runnable_script()`, which
turns it into a standalone script the sandbox executes — no fixture-
specific code anywhere in `system/` or in `regression/verify.py`. That's
deliberate: the pipeline is supposed to generalize across vulnerability
classes, not special-case one demo.

### 1. `fixtures/netdiag.py` — command injection (`shell_exec`)

A tiny "ping a host" CLI. `vulnerable()` builds the shell command with an
f-string: `os.system(f"ping -c 1 {host}")`. Anything in `host` that a
shell treats specially — `;`, `&&`, `|`, backticks, `$()`, even an
embedded newline — runs as a second, attacker-chosen command. `fixed()`
validates `host` against a strict hostname/IP regex, then calls
`subprocess.run(["ping", "-c", "1", host], shell=False)` — no shell ever
parses the argument, so metacharacters are just literal text ping doesn't
understand.

This is the most common real-world sink: anywhere a script "just" shells
out to a system binary with a string built from user input (`ping`,
`curl`, `convert`, `git`, ffmpeg wrappers — the list is long). It's
usually introduced by someone reaching for `os.system()` because it's the
first thing that works, not by malice.

### 2. `fixtures/sql_injection.py` — SQL injection (`sql_query`)

`vulnerable()` string-interpolates a `name` parameter into
`cursor.executescript(f"SELECT * FROM users WHERE name = '{name}'")`.
A payload like `x'; ATTACH DATABASE '/tmp/kagutsuchi_pwned' AS pwn;
CREATE TABLE pwn.t(x); --` closes the intended string early, then chains
two more SQL statements the attacker wrote. `fixed()` uses a single
parameterized call, `cursor.execute("...WHERE name = ?", (name,))` — the
database driver binds the payload as one opaque value, never as SQL
syntax, so there's nothing to "close early."

This is the textbook injection class (the "Bobby Tables" one), and it's
still one of the most common vulnerabilities in real applications because
string-building a query is the naive-but-obvious way to write one.

One thing worth knowing if you're narrating a live demo: `vulnerable()`
also breaks on a *benign* name containing an apostrophe (e.g. `"O'Brien"`)
— it throws a `sqlite3.OperationalError` instead of quietly misbehaving.
That's not a bug in the fixture; it's the exact real-world symptom of
this vulnerability class (the classic bug report of "customers named
O'Brien can't sign up"). If you're demoing live, use a clean name like
`alice` for the "this also works normally" beat, not one with a quote in
it.

### 3. `fixtures/insecure_deserialization.py` — insecure deserialization (`deserialization`)

`vulnerable()` calls `pickle.loads()` on base64-decoded, attacker-supplied
bytes. Pickle isn't a data format like JSON — it's a small bytecode
language for reconstructing arbitrary Python objects, and it has a
supported hook, `__reduce__`, that lets a crafted object specify *any
callable to run with any arguments* as part of being unpickled. So
"deserializing untrusted data" with pickle is not "parsing might fail" —
it's "arbitrary code execution," full stop. `fixed()` uses `json.loads()`
instead: JSON has no equivalent hook, so a malicious payload is either a
decode error or inert plain data, never a code path.

This is the class most people underestimate, because reaching for
`pickle` feels like reaching for any other serialization format. It's
worth including here for exactly that reason — the point of the demo is
partly to show the pipeline isn't tuned to one obvious "stringly-typed"
injection pattern.

### Why all three use the same observable proof

Every attack payload's goal is to make one specific file appear:
`/tmp/kagutsuchi_pwned`. Command injection does it with `touch`. SQL
injection does it by chaining `ATTACH DATABASE '/tmp/kagutsuchi_pwned'`
onto the query, which makes SQLite create that file on disk. Insecure
deserialization does it via a pickled `__reduce__` that calls `eval(...)`
to run the same `touch`. Three completely different mechanisms, one
shared, boring, unambiguous "did the exploit actually run" signal — which
is what let `regression/verify.py` stay a few lines of file-diff checking
instead of growing a special case per vulnerability class (see below).

## Hypothesis generation and the fallback pattern (`hypothesis/`)

Given a `SecurityFinding`, `hypothesis/generate.py::generate()` asks Groq
for one concrete `AttackHypothesis`: a security property, an attack
vector description, a single payload, and what the evidence should look
like if the code is vulnerable vs. safe. It's a single call with
`temperature=0` — this is deliberately not a fuzzer or a multi-turn
"let's try things" agent. One hypothesis, one payload, byte-identical
before and after, because the demo's entire credibility claim rests on
replaying the *exact same* input both times.

The important design decision is what happens when Groq **doesn't**
answer — rate-limited, network blip, malformed JSON, or a well-formed
response with a field of the wrong type. `generate()` catches all of
those (`GroqUnavailable`, `KeyError`, `TypeError`, and
`pydantic.ValidationError` for the "valid JSON, wrong shape" case) and
falls back to a hardcoded `AttackHypothesis` instead of raising. Each
fixture has its own fallback (`hypothesis/fallback.py`,
`sql_fallback.py`, `deserialization_fallback.py`) — this used to be a
single hardcoded fallback that only knew about the netdiag payload, which
silently gave the *wrong* hypothesis to the other two fixtures if Groq
ever hiccuped. `generate()` now takes the matching fallback as a
parameter (defaulting to netdiag's, for the original call sites that
don't know about the other fixtures).

Why bother at all, instead of just letting a live demo depend on a live
API call? Because "the LLM was down" is not an acceptable reason for a
security verification demo to fail on stage, and because a rate limit hit
mid-hypothesis-generation shouldn't be indistinguishable from "the
pipeline is broken." The fallback hypothesis is the *exact* same payload
a healthy Groq call would very likely produce anyway (we know, because
we've run it both ways) — so falling back doesn't mean the demo becomes
less real, it means it becomes deterministic. That's a feature, not a
compromise: the actual verdict still comes from real code executing in a
real container, never from the LLM's opinion.

## `regression/verify.py` — deliberately dumb, on purpose

`verify()` takes an `AttackHypothesis` and a before/after pair of
`ExecutionEvidence`, and produces a `VerificationResult` with one of four
verdicts: `VERIFIED_FIXED`, `STILL_VULNERABLE`, `FALSE_POSITIVE`, or
`INCONCLUSIVE`. The whole function is maybe 40 lines, and that's
intentional. It does exactly two things:

1. Checks `before.run_id == after.run_id` — if the two pieces of evidence
   didn't come from the same paired run, the comparison is meaningless,
   so it returns `INCONCLUSIVE` rather than guessing.
2. Checks whether `/tmp/kagutsuchi_pwned` is in `filesystem_diff["created"]`
   for each phase, and maps `(before_vulnerable, after_vulnerable)` onto
   one of the four verdicts.

That's it. No stdout parsing, no LLM asked "did this work?", no fuzzy
scoring. The verdict is a fact about the filesystem, derived the same way
regardless of which of the three (or a future fourth, fifth...)
vulnerability classes produced the evidence. That's the actual point of
Kagutsuchi's pitch — "an explanation is not an exploit, and 'looks fixed'
is not a verdict" — and it only holds up if the verdict-deriving code
itself can't be talked into a favorable answer. A dumb, evidence-only
comparator is a feature: it's the part of the system a judge should trust
*because* it's boring.

The one subtlety worth calling out: `_marker_created()` doesn't just
check "was anything created." A real Docker container creates ~25
incidental `.pyc` bytecode-cache files plus `/workspace` and
`/workspace/candidate.py` on every single run, exploit or not — that's
just Python compiling its standard library imports the first time they're
used inside a fresh container. The first real Docker run of this pipeline
came back `STILL_VULNERABLE` for a fix that actually worked, because an
earlier version of this check treated "created is non-empty" as "exploit
succeeded." Mocked/local tests never surfaced this, because the local,
non-Docker attack runner (`attacks/run_local.py`) only ever reports the
exact marker path, with no container-startup noise to obscure it. Fixed
by checking for the specific marker path, not "created is non-empty" —
see `test_incidental_docker_files_do_not_count_as_the_marker` for the
regression test that locks this in.

## A cross-platform bug that only a real Docker run could catch

Worth writing up properly, because it's a genuinely good illustration of
why "prove it on real infrastructure" matters even for the tooling that
does the proving.

The deserialization fixture's attack payload is a base64-encoded pickle
stream. My first version built it with `__reduce__` returning
`(os.system, ("touch /tmp/kagutsuchi_pwned",))` — pickle a reference to
the function `os.system`, plus its argument, so unpickling calls it. This
worked perfectly when I tested it locally. It failed the moment it ran
against the real Docker sandbox, with:

```
ModuleNotFoundError: No module named 'nt'
```

The cause: pickle doesn't store "the function called `system` that lives
on the `os` module" — it stores the function's *actual* `__module__` and
`__qualname__`, and looks the callable up by re-importing that module at
unpickle time. `os.system` isn't actually defined in `os.py`; the `os`
module does `from nt import *` on Windows (or `from posix import *` on
Linux/macOS) and re-exports the platform module's functions. So
`os.system.__module__` reports `'nt'` on the machine that pickled it —
this dev environment is Windows — and when that pickle stream is
unpickled inside the Linux sandbox container, Python tries to import a
module called `nt`, which simply doesn't exist there. A completely
correct exploit, that would have worked fine if generated on Linux, was
silently broken by *the OS I happened to build it on*.

No local test caught this, because "does the payload's `__reduce__`
resolve" is invisible until something actually unpickles it in an
environment where the reference might not resolve — and my local
Windows tests were, of course, running on the same OS I built the payload
on. It surfaced immediately on the first real-Docker attempt, as a plain
`ModuleNotFoundError` in the container's stderr.

The fix: route the exploit through `eval` instead —
`(eval, ("__import__('os').system('touch /tmp/kagutsuchi_pwned')",))`.
`eval` is a builtin, and builtins pickle under the stable `builtins`
module on every platform, so there's no OS-specific module reference to
break. Same effect (arbitrary code execution during unpickling), no
platform coupling.

The broader point, and the reason this is worth more than a one-line
changelog entry: this project's entire pitch is that mocked tests and
"looks correct" reasoning aren't good enough evidence for a security
claim — you have to actually run the exploit and watch what happens. That
principle turned out to apply to *building the exploits themselves*, not
just to the vulnerable code they target. If I'd only ever tested this
fixture against local mocks, I would have shipped a broken payload and
never known.

## Directory layout

```
verification/
├── fixtures/              the three vulnerable()/fixed() pairs
├── hypothesis/            Groq-based generation + per-fixture hardcoded fallbacks
├── attacks/
│   ├── run_local.py       non-Docker attack runner, for testing without system/sandbox
│   └── payload_variants.py  extra injection payloads proving netdiag isn't only
│                             exploitable one specific way
├── evidence/fakes.py      hand-written fake ExecutionEvidence, for testing
│                          regression/ without waiting on a real sandbox run
├── regression/verify.py   the marker-based comparator described above
├── models.py              re-exports contracts/ types (see note below)
├── pipeline.py            score() — single entry point wiring generate() + verify()
└── tests/                 ~55 tests; run with `pytest verification/tests`
```

`models.py` used to define its own independent copy of the four contract
types; it now just re-exports from `contracts/`, so there's one source of
truth for the `SecurityFinding` / `AttackHypothesis` / `ExecutionEvidence`
/ `VerificationResult` shapes that both halves of the system share.

## Running the tests

```
pip install -r verification/requirements.txt
pytest verification/tests
```

A handful of tests are skipped on non-POSIX systems (this was developed
partly on Windows) — anything that actually shells out via `os.system`,
attaches a SQLite database to `/tmp/...`, or expects a POSIX-style path
only runs where that's meaningful, i.e. Linux/macOS or inside the Docker
sandbox itself. The `fixed()` side of every fixture — the side that
matters for proving the vulnerability is closed — runs everywhere.
