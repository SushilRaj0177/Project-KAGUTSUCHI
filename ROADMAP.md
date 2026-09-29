# Roadmap

Honest status tracking — a milestone is only checked off once it's real,
tested code, the same standard the rest of this project holds itself to.
No milestone is marked done because a plan for it exists.

- [x] **M0 — Dismantle & inventory.** Project KAGUTSUCHI's engine (sandbox,
      analysis, verification, integration, webapp, deploy tooling, tests)
      moved intact into `engine-archive/kagutsuchi/`, with a README mapping
      each piece to the milestone that reintroduces it. Nothing deleted;
      nothing left half-migrated. New repo root established with
      `ARCHITECTURE.md` grounding every future decision in cited,
      verifiable research.
- [x] **M1 — Foundation.** `wsqfai/domain/quality_model.py`: ISO/IEC
      25010:2011's 8 characteristics + real sub-characteristics, plus
      ISO/IEC 25059:2023's AI-specific additions (Functional Adaptability,
      User Controllability, Transparency, Intervenability, Societal and
      Ethical Risk Mitigation), each sourced and cited, not invented.
      `wsqfai/domain/evidence.py`: the canonical `Finding` / `Evidence` /
      `Observation` / `AIAssessment` model — a Finding must cite a real,
      correctly-scoped sub-characteristic and at least one Evidence item,
      enforced by validation, not convention.
      `wsqfai/ingestion/repository.py`: real repo cloning (safety pattern
      carried over from KAGUTSUCHI's proven server/repo_scan.py, extended
      from Python-only to any language) and file/language classification.
      19 tests, including one real end-to-end clone against a live public
      GitHub repo (skipped, not faked, if network is unavailable).

      **Bug found and fixed later (during M7):** `requirements.txt` and
      `.toml` files had no recognized extension, so their content was
      never retained by ingestion - silently breaking the Portability
      check (M2b) against every real repository since the day it shipped,
      even though its own unit tests passed (they constructed `FileRecord`
      directly, bypassing real ingestion, and never caught it). Fixed by
      adding `.toml` as a real classified extension (consistent with YAML/
      JSON already being classified) and a small filename allowlist for
      extension-less manifests (`requirements.txt`, `Pipfile`, `Dockerfile`,
      `Makefile`). Caught by actually running the tool against Flask's
      real repository and noticing zero Portability findings where there
      should have been some - a reminder that a unit-test suite passing is
      not the same as the pipeline working end to end, which is exactly
      why `wsqfai/report.py` exists. 2 regression tests added.
- **M2 — SQuaRE quality measurement.** Deterministic measurement of real
      SQuaRE product-quality characteristics — each metric traceable to the
      specific sub-characteristic it measures. Split honestly into slices
      rather than checked off as one lump, since only one slice is real so
      far:
  - [x] **M2a — Maintainability slice.** `wsqfai/measurement/maintainability.py`:
        deterministic, structural metrics against a `RepositorySnapshot`
        for three Maintainability sub-characteristics — Modularity
        (god-file line-count thresholds, the same order of magnitude
        Checkstyle/PMD use by default), Analysability (average
        characters-per-line, catching minified/generated code a human or
        AI reader would struggle with), and Testability (ratio of
        test-file-convention matches to code files, explicitly labelled a
        structural proxy, not real coverage). Every Finding cites a real
        `sub_characteristic_key` and at least one Evidence item pointing
        at the file(s) that produced it. 12 tests, including one real
        end-to-end run against a live cloned public repo. Deliberately
        scoped to what `RepositorySnapshot` can measure without
        re-reading file content (path/language/size/line-count only) —
        see the module's own docstring for why that's a stated
        limitation, not an oversight.
  - [x] **M2b — Remaining SQuaRE characteristics.** Reliability, Performance
        Efficiency, Compatibility, Usability, Portability — all five now
        have a real, tested static signal:
    - [x] **Reliability (Fault Tolerance).** `wsqfai/measurement/reliability.py`:
          real Python AST-based detection (not text/regex matching, which
          would misfire inside strings/comments) of bare `except:` clauses
          (HIGH — catches SystemExit/KeyboardInterrupt/GeneratorExit too,
          not just the intended fault) and swallowed `except Exception`/
          `except BaseException` handlers whose body is only `pass` (MEDIUM
          — a fault occurred and the system proceeds as if it hadn't). A
          broad handler that logs, re-raises, or returns is correctly left
          unflagged — the breadth of the catch isn't the problem, silently
          discarding the fault is. 9 tests.
    - [x] **Portability (Installability).** `wsqfai/measurement/portability.py`:
          detects fully unpinned dependencies in `requirements.txt` and
          `pyproject.toml`'s `[project.dependencies]` (parsed with the
          stdlib `tomllib`, not regex) — a dependency with no version
          operator at all can silently resolve to a different, untested
          version on a fresh install, ISO/IEC 25010's Installability
          sub-characteristic. Deliberately narrow: any version operator at
          all (even a loose `>=`) is treated as constrained, since the
          goal is catching completely unconstrained dependencies, the
          clearest low-false-positive signal, not grading pin strictness.
          9 tests.
    - [x] **Usability (Appropriateness Recognizability).**
          `wsqfai/measurement/usability.py`: flags a repository with no
          README (`README`/`README.md`/`README.rst`/`README.txt`) at its
          root. A prospective user has nothing to read before deciding
          whether the project is relevant to their needs otherwise - the
          same signal GitHub's own community-standards checklist uses, not
          an invented rule. Deliberately checks presence only, not content
          quality: a one-line README still clears it, since judging
          content quality is beyond what a static check can honestly claim.
          7 tests.
    - [x] **Performance Efficiency (Time Behaviour) — one narrow, real
          static signal.** `wsqfai/measurement/performance.py`: AST-based
          detection of `x = x + <expr>` / `x += <expr>` executed inside a
          loop body where the expression gives strong static evidence of
          building a string (an f-string, a string literal, or a
          `str(...)` call). Because Python strings are immutable, each
          such iteration allocates an entirely new string and copies the
          old contents in — O(n) work per iteration, O(n^2) total — a
          well-established anti-pattern (the reason `"".join(...)` exists,
          and the same class of issue `perflint`, a real published static
          analyzer, flags). Correctly leaves numeric accumulation
          (`total += price`) unflagged. 8 tests. Most of Time Behaviour/
          Resource Utilization/Capacity still genuinely can't be measured
          from static source alone — this is one real, narrow exception.
    - [x] **Compatibility (Co-existence).** `wsqfai/measurement/compatibility.py`:
          AST-based detection of a literal integer passed as `port=` to
          any call (`app.run(port=5000)`, `uvicorn.run(app, port=8000)`) —
          a service that hardcodes the port it binds to can't share a host
          with another instance of itself, or an unrelated service wanting
          the same port, without the user first editing the source (the
          Twelve-Factor App methodology's "Config" factor names port
          binding as its canonical example). Not framework-specific:
          scoped to the `port=` keyword itself. `port=int(os.environ.get(
          "PORT", 5000))` is a `Call`, not a bare `Constant`, so it's
          correctly left alone — the port is already configurable there.
          Test files excluded. 9 tests.

          **Bug found and fixed later (during a follow-up session):** both
          of these modules' `compute_*_findings` functions were imported
          into `wsqfai/report.py` but never actually called in
          `analyze_snapshot`'s extend() chain — almost certainly dropped
          during a manual GitHub-web merge-conflict resolution on that
          exact block of code, across two PRs merged close together. Every
          test in each module's own suite passed throughout, since none of
          them exercise `analyze_snapshot` itself; this ROADMAP entry also
          silently reverted to "not started" the same way. Caught by
          constructing a synthetic repository that should trigger both
          checks and finding zero matching findings in the real report
          output. Fixed by restoring both `findings.extend(...)` calls and
          adding `test_analyze_snapshot_wiring_covers_every_implemented_
          characteristic` to `tests/test_report.py` — a test specifically
          designed to catch "the module works in isolation, but nothing
          calls it," which no existing test did. Verified it would have
          caught the bug by reverting the fix and re-running it.

          Also added a cheaper, generic backstop against the same class of
          bug for any future module: `tests/test_lint.py` runs `pyflakes`
          across the whole `wsqfai` package and fails on any unused
          import or undefined name — an import nobody uses is almost
          always a sign something was wired in, then silently unwired.
          New `lint` optional-dependency group (`pip install -e
          ".[lint]"`); the test skips rather than fails if it isn't
          installed. Verified it actually flags this exact bug shape by
          re-simulating the dropped `findings.extend(...)` call and
          confirming `pyflakes` reports the now-unused import.
- **M3 — AI/ML quality extension.** ISO/IEC 25059 characteristics for
      ML-containing repositories, plus the ML design-pattern
      detection/recommendation engine, grounded in Washizaki et al.'s own
      catalogue (IEEE Computer, Vol. 55 No. 3, March 2022: 12 ML
      architecture patterns, 13 ML design patterns, 8 ML anti-patterns,
      itself building on Sculley et al.'s "Hidden Technical Debt in
      Machine Learning Systems", NeurIPS 2015). Split into slices for the
      same reason M2 was:
  - [x] **M3a — ML-repository detection + ML Versioning check.**
        `wsqfai/measurement/ml_patterns.py`: `is_ml_repository()` detects
        real, direct imports of a general-purpose ML/DL framework
        (scikit-learn, PyTorch, TensorFlow/Keras, XGBoost, LightGBM,
        CatBoost, Transformers, JAX) — deliberately excluding bare
        numpy/pandas usage as too weak a signal. For ML-containing repos,
        checks for a real "ML Versioning" signal (Washizaki's cataloged
        good pattern) — DVC config, MLflow/model-registry usage, or a
        versioned artifact filename (`*_v<N>.<ext>`) — and flags a
        Maintainability/Modifiability Finding, citing the pattern by name
        and source, when none is found. 9 tests. This required extending
        `wsqfai/ingestion/repository.py`'s `FileRecord` to retain each
        classified file's text content (previously discarded right after
        line-counting) — a real, deliberate scope change to M1's
        ingestion layer, covered by 2 new tests there (34 → all still
        passing).
  - **M3b — Remaining catalogue patterns/anti-patterns.** Glue Code,
        Pipeline Jungles, Dead Experimental Codepaths, Test Infrastructure
        Independence, Wrap Black-box Packages into Common APIs, and the
        rest of the 12+13+8 catalogue. Each needs a detection heuristic
        honest enough not to be mostly false positives from a static,
        no-execution read of source — that's real design work per
        pattern, not a batch of regexes to add in one sitting.
    - [x] **Dead Experimental Codepaths.** `wsqfai/measurement/ml_patterns.py`:
          AST-based detection of `if False:`/`if 0:` branches containing
          real code (not just `pass`/a docstring) in an ML-containing
          repository. Sculley et al.'s "Hidden Technical Debt in Machine
          Learning Systems" (NeurIPS 2015) names this exact pattern — an
          alternative approach tried behind a conditional that's later
          disabled rather than removed, accumulating as debt that obscures
          what the system does. The lowest-false-positive instance of this
          pattern a static, no-execution read can identify: a literal
          `False`/`0` condition can never be true regardless of any runtime
          state, so no semantic analysis is needed to know the branch is
          dead. ISO/IEC 25010's Analysability sub-characteristic. 4 tests.
    - [ ] Glue Code, Pipeline Jungles, Test Infrastructure Independence,
          Wrap Black-box Packages into Common APIs, and the rest of the
          12+13+8 catalogue — still need their own honest scoping pass.
  - [ ] **M3c — ISO/IEC 25059 AI-specific characteristics themselves**
        (Functional Adaptability, User Controllability, Transparency,
        Intervenability, Societal/Ethical Risk Mitigation from
        `quality_model.py`) — these need signals beyond static structure
        (e.g. whether a model-serving endpoint exposes an explanation/
        override mechanism), which is further scoping work, not yet
        started.
- **M4 — Security, proven not asserted.** Reintroduce
      `engine-archive/kagutsuchi`'s sandbox + attack-hypothesis + verify
      pipeline, re-platformed onto the new Finding/Evidence model, findings
      framed via the AI Security Continuum's dimensions. Split for the same
      reason M2/M3 were:
  - [x] **M4a — Static hypothesis generation.** `wsqfai/security/ast_scan.py`
        re-platforms `engine-archive/kagutsuchi/system/analysis/ast_scan.py`'s
        AST-based sensitive-operation scanner (shell exec, subprocess,
        deserialization, SQL/Django/YAML/SSTI injection heuristics, all
        gated by a taint-propagation check so a dangerous call built from
        only hardcoded arguments isn't flagged) onto wsqfai's domain model
        — detection logic carried over near-verbatim since it was already
        proven against real code, only its *output* changes. Every hit
        becomes an `Observation`, deliberately NOT a `Finding`: a static
        AST match is evidence of a pattern, not proof of a vulnerability,
        and minting a Finding from it would violate this project's own
        "proven, not asserted" discipline (ARCHITECTURE.md's #1 security
        design decision). `wsqfai/security/scanner.py` runs it across a
        whole `RepositorySnapshot`. Also captures each function's own
        source, its enclosing file's module-level imports, and (for the
        narrow shape M4b needs) which single parameter directly carries
        the tainted data into the sink. 30 tests (27 detector-level, 3
        repository-level), ported from the archive's own
        `tests/system/test_ast_scan.py` test-by-test. `LearnedSignature`/
        `extra_signatures` and `scan_diff`/diff-scoped scanning were left
        out of this port deliberately — they depended on a review/approval
        workflow and a CI diff view that haven't been re-platformed yet.
  - [x] **Hardcoded credential detection (new, not in the archive).**
        `wsqfai/security/secrets.py`: unlike everything else in this
        module, this mints a real `Finding` directly, not an `Observation`
        — a hardcoded secret literal *is* the complete evidence, there's
        nothing to sandbox-verify (whether the string is exploitable
        doesn't depend on runtime behavior the way command injection
        does). Flags a plain string-literal assignment to a credential-
        shaped variable name (password/secret/api key/access key/private
        key/auth token), the same practice Bandit's B105-B107 rules and
        secret scanners like gitleaks/truffleHog use. Deliberately
        excludes obvious placeholders (`changeme`, `<your-key-here>`,
        anything under 8 characters) and test files, to keep the false-
        positive rate low. The Finding's own evidence snippet redacts the
        actual value (`name = <redacted>`) — the report itself must never
        become a secondary leak vector for the secret it just found. 12
        tests, ISO/IEC 25010's Confidentiality sub-characteristic.
  - [x] **M4b — Sandbox verification (shell-exec slice).**
        `wsqfai/security/sandbox.py` re-platforms
        `engine-archive/kagutsuchi/system/sandbox/subprocess_runner.py`:
        real, isolated subprocess execution (rlimits, a scrubbed
        environment, serialized runs) plus `wsqfai/security/landlock.py`
        (`.../system/sandbox/landlock.py`, real kernel-level Landlock
        confinement — filesystem writes restricted to a scratch dir,
        outbound TCP denied — verified against the actual kernel in this
        environment, not mocked: 13 tests, none skipped). Docker isolation
        (`docker_runner.py`) was deliberately NOT re-platformed — it needs
        a reachable Docker daemon this environment doesn't provide, and
        reintroducing untested orchestration code would be exactly the
        vaporware this project's honesty discipline forbids.

        `wsqfai/security/verify.py` is the actual "prove it" step: for the
        one mechanically reconstructible shape this slice covers — a
        direct shell-exec call (`os.system`/`os.popen`) in a function with
        exactly one parameter, where the tainted data reaches the sink
        directly (no intermediate local variable) — it builds a
        self-contained candidate script from the observed function's real
        source, actually runs it in the sandbox with a shell-injection
        payload, and only mints a `Finding` when the sandbox proves the
        injection executed (a marker-file side effect). This generalizes
        Project KAGUTSUCHI's own demo, which only ever proved this against
        three hand-authored fixtures: the same static pattern in two
        *different* real functions — one genuinely vulnerable, one that
        validates its input first — is correctly told apart by actually
        running both, not by trusting the identical AST match. Every other
        Observation shape (SQL injection, deserialization, SSTI, multi-
        parameter shell-exec, taint through a local variable) returns
        `NOT_APPLICABLE` — a stated limitation, not a silent false
        negative. 10 tests, plus 2 in `wsqfai/report.py`'s own suite proving
        the wiring: a confirmed hypothesis is promoted to a `Finding`, an
        unsupported one stays a hypothesis.

        **Widened later:** `subprocess.run`/`Popen`/`call` with an explicit
        `shell=True` keyword is now verifiable too — `ast_scan.py` records
        whether the call site passes `shell=True`
        (`Observation.metadata["shell_true"]`), and `verify.py` attempts
        the same generic shell-metacharacter payload against it, since
        `shell=True` means the command genuinely reaches a real shell
        (unlike plain `subprocess.run(argv)`, which execs directly and
        stays unverifiable). 4 new tests (2 in `ast_scan`, 2 in `verify`,
        including a real sandbox-confirmed end-to-end run).

        **Widened again:** direct `eval`/`exec` calls (single-parameter,
        no intermediate local variable, same taint discipline as the
        shell shapes) are now verifiable too — a Python-source payload
        (`__import__('pathlib').Path(<marker>).touch()`) proves code
        execution the same way the shell-metacharacter payload proves
        command injection, since eval/exec run their argument as code no
        matter what the function otherwise does with it.
        `verify_shell_exec_observation` was renamed to
        `verify_security_observation` to match — it now verifies three
        shapes, not one — and `promote_to_finding` labels the resulting
        Finding "code execution" with `rule_id
        sandbox_verified_code_execution`, distinct from the shell shapes'
        "command injection" / `sandbox_verified_shell_injection`, so the
        two vulnerability classes never get conflated in a report. Sanity-
        checked against `pallets/flask`: its own `exec()` usage in
        `config.py` (a multi-parameter shape) correctly stays an
        unverified hypothesis, not a false "Proven" finding. 6 new tests,
        including two real sandbox-confirmed end-to-end runs.

        pickle.loads/marshal.loads (also `SensitiveOp.DESERIALIZATION`,
        but taking a serialized data blob rather than directly executing
        a source string) remain unverifiable by this slice — constructing
        an actual malicious pickle payload as a plain argv string is real
        further work, not attempted here. SQL injection, SSTI, multi-
        parameter calls, and taint through a local variable also stay
        `NOT_APPLICABLE`. Reintroducing the archived LLM-based hypothesis
        generation (`verification/hypothesis/generate.py`,
        `groq_client.py`) to widen coverage further is real further M4b
        work.
  - [ ] **M4c — AI Security Continuum framing.** Reframe M4a/M4b findings
        via Washizaki & Yoshioka's multi-dimensional continuum (CAIN 2024)
        instead of flat severity tags.
- **M5 — Evidence & benchmark engine.** WSQF/WSQB-style benchmarking: build
      a small reference corpus of scanned repositories and report a repo's
      measurements *relative to that corpus*, not as a lonely number.
  - [x] **M5a — Comparison methodology.** `wsqfai/benchmark.py`:
        `CorpusReport.findings_per_kloc_by_characteristic()` computes a
        corpus-wide findings-per-1000-lines rate per characteristic,
        weighted by each repo's own line count (summing counts and lines
        separately, never averaging per-repo rates) so one huge repository
        isn't drowned out by many tiny ones. `compare_to_corpus()` then
        expresses a single report as a ratio against that baseline (1.0 =
        average, 2.0 = twice the corpus rate), returning `None` rather
        than a bogus infinity when the corpus has zero findings for that
        characteristic to divide by. 6 tests, including one real
        end-to-end corpus build against a live public repo. This was the
        *methodology* proven correct, not the whole milestone finished at
        the time - `compare_to_corpus` still takes any `CorpusReport`
        a caller supplies, including a custom one; M5b adds a real curated
        default.
  - [x] **M5b — A real reference corpus.** `wsqfai/reference_corpus.py`:
        a curated, versioned list of 4 real, actively-maintained,
        permissively-licensed repositories - `pallets/flask` (web
        framework), `psf/requests` (HTTP client), `pallets/click` (CLI
        toolkit), `benoitc/gunicorn` (WSGI server) - deliberately diverse
        in application shape, not just four web frameworks, since diversity
        is what makes `compare_to_corpus()`'s baseline mean something
        rather than secretly measuring "typical of web frameworks." Each
        entry carries its own one-line justification inline, so the
        corpus's composition stays auditable. `build_reference_corpus()`
        caches the built `CorpusReport` to a JSON file (via pydantic's own
        `model_dump_json`/`model_validate_json`) so repeated benchmark runs
        don't re-clone and re-analyze all 4 repositories every time - only
        `force_refresh=True` (e.g. after `REFERENCE_CORPUS` itself changes)
        rebuilds and overwrites the cache. Deliberately small (4, not
        WSQF/WSQB's 21): a small set that's actually exercised end-to-end
        beats a large one that's aspirational. 8 tests, including one real
        end-to-end build against all 4 live repositories, cached, then
        confirmed the cache is read back without a second clone.
- [ ] **M6 — Dashboard, report, CI/PR integration.** A real frontend
      (reusing KAGUTSUCHI's auth/i18n infrastructure from the archive where
      it fits), a generated report, and a CI-gate mode.
- **M7 — Remediation: "clean it up," not just "here's what's wrong."**
      Added after real feedback that a findings-only report isn't useful
      enough on its own - overlaps with what free linters already do
      unless it actually fixes something.
  - [x] **M7a — Mechanical auto-fix (first two rules).** `wsqfai/remediation.py`:
        for a Finding whose fix is unambiguous and mechanical, generate a
        real unified diff from the repository's own actual file content -
        `git apply`-able, not a generic snippet. Covers `bare_except`
        (narrow to `except Exception:`) and `unpinned_dependency` (pin to
        the dependency's real current release, looked up live from PyPI).
        Deliberately does NOT auto-fix a sandbox-confirmed security
        Finding (`sandbox_verified_shell_injection`) - correctly rewriting
        a shell-exec call needs understanding the intended command, which
        this tool doesn't have, so it returns human-actionable guidance
        text instead of a diff it can't stand behind. Wired into
        `wsqfai/report.py`: every report now carries `fixes`/`suggestions`,
        and `RepositoryReport.combined_patch()` (CLI: `wsqfai <repo>
        --patch`) gives one patch file for everything auto-fixable at
        once. 13 tests plus 2 in `report.py`'s own suite. Required
        splitting `wsqfai/measurement/portability.py`'s findings from one
        aggregated-per-file Finding to one per unpinned dependency (with a
        real line number) - each fix needs its own precise line to edit,
        which an aggregated summary string couldn't provide.
  - [x] **M7b — Wider fix coverage.** `pyproject.toml`'s unpinned
        dependencies now get real per-entry line numbers - tomllib doesn't
        expose array-entry line numbers, so `portability.py` recovers them
        with a narrow raw-text scan of the `[project]` table's
        `dependencies = [...]` array, falling back to the old aggregated
        Finding if the scan can't place every entry tomllib itself reports
        as unpinned (an escaped-character mismatch, an unrecognized array
        shape) rather than guessing a wrong line. `swallowed_broad_exception`
        gets a `Suggestion` (log the fault, consider re-raising) rather than
        an auto-fix - safely inserting a logging call needs to know whether
        the file already imports `logging`, and whether the swallow was
        ever actually intentional is a judgment call this tool can't make.
        164 -> 168 tests. Anything else M2b/M3b add later stays open.
  - **M7c — A real, running web app.** `engine-archive/kagutsuchi/webapp`
        + `server/` already built exactly this shape once (paste a repo
        link, get a report back) - reconnecting them onto this pipeline is
        what turns "run a CLI" into "paste a link on a website," which is
        the actual product experience, not just a demo screenshot. Split
        into backend (real, done) and frontend (not started):
    - [x] **M7c-backend.** `wsqfai/server/main.py` re-platforms
          `engine-archive/kagutsuchi/server/main.py`'s design: a real
          FastAPI app with `/api/analyze-repo/start` + `/api/analyze-repo/
          jobs/{job_id}` (a background-job pattern, ported near-verbatim
          from `server/jobs.py` - exists because a real repo scan can take
          longer than a typical serverless proxy's request timeout, which
          caused a live 504 in the original product) and `/api/open-pr`
          (opens a real GitHub PR carrying the selected Fixes, via
          `wsqfai/integration/github_pr.py` - re-platformed from
          `integration/github_pr.py`, generalized from "one function fix
          per PR" to "every fix from a scan in one PR"). Per-IP rate
          limiting ported near-verbatim from `server/rate_limit.py`. 18
          tests (10 server, 8 github_pr - the GitHub API itself is mocked
          at the network boundary, since a test suite can't safely make
          real write calls against arbitrary repos). Manually smoke-tested
          for real: started the server with uvicorn, submitted a real
          `octocat/Hello-World` scan over HTTP, and polled it to
          completion. Uses stdlib `urllib`, not the `requests` package -
          matches `remediation.py`'s PyPI lookup, no new HTTP dependency.
    - [x] **M7c-frontend (analyze flow).** `webapp/app/analyze/page.tsx`
          + `webapp/app/lib/api.ts`: a real page on the marketing webapp
          that calls the actual backend - paste a public GitHub URL,
          submit, and the browser does the same
          `POST /api/analyze-repo/start` -> poll
          `GET /api/analyze-repo/jobs/{job_id}` round-trip the CLI's
          `--json` mode exercises, then renders the real
          `RepositoryReport` (findings table, security hypotheses table,
          proposed fixes with their real diffs, a client-built "download
          patch" combining every fix's diff the same way
          `RepositoryReport.combined_patch()` does server-side). No new
          backend logic - `wsqfai/server/main.py` was already real and
          proven (M7c-backend); this is the first thing in the browser
          that actually calls it, closing "paste a link on a website"
          instead of "run a CLI". `NEXT_PUBLIC_API_BASE_URL` (see
          `webapp/.env.example`) points the webapp at the backend -
          defaults to `http://localhost:8000` for local dev. Manually
          driven end-to-end with Playwright against a real running
          backend: submitted `octocat/Hello-World` (0 findings) and
          `pallets/click` (11 findings, 7 security hypotheses, 4
          suggestions) and confirmed both rendered correctly from a real
          HTTP round-trip, not a mock.

          Deliberately not done yet: this doesn't replace the CLI as the
          only way to get a report, doesn't add GitHub OAuth or a "paste
          a token" flow for `/api/open-pr` (opening the fix PR from the
          browser), and the backend itself isn't deployed anywhere
          public yet - `webapp/` is on Vercel, but `wsqfai/server/`
          still only runs via `uvicorn` wherever someone starts it. Real
          next steps: deploy the backend somewhere with a stable HTTPS
          URL, set `WSQFAI_ALLOWED_ORIGINS` to the deployed webapp's
          origin instead of the wildcard default, and point Vercel's
          `NEXT_PUBLIC_API_BASE_URL` at it. Wiring `/api/open-pr` into
          the UI (with GitHub OAuth replacing the raw-token MVP) is
          separate further work.

## Immediately next

M7c-frontend's core analyze flow is now real - paste a link on the
website, get the same report the CLI produces, proven end to end against
live repositories. What's left of it is deployment, not code: the
backend needs a stable public URL before the deployed webapp (Vercel) can
actually reach it, and `/api/open-pr` still needs a UI plus a decision on
GitHub OAuth vs. the "paste a token" MVP. Independent of that: the core
"proven, not asserted" loop is real
end to end - ingest a repo, statically hypothesize (M4a), actually attempt
the exploit in a kernel-confined sandbox (M4b), and only mint a Security
Finding when the sandbox proves it - `wsqfai/report.py`'s own tests
demonstrate the same static pattern in two different real functions
correctly resolving to two different verdicts. The highest-value next step
there is widening M4b's coverage beyond its three current shapes
(reintroducing `verification/hypothesis`'s LLM-based hypothesis
generation, constructing real pickle payloads, or handling multi-parameter
functions), since that's what
turns this from "one narrow
but real case" into something that finds proven vulnerabilities across a
meaningfully wider slice of real code. M3b/M3c/M4c's other remaining
slices are all real, scoped, startable work whenever picked up.
