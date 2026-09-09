# Shared Contracts (v0.1 — SEED)

These four types are the **only** integration surface between the two
workstreams. `system/` produces/consumes some of them, `verification/`
produces/consumes the rest — neither side needs to read the other's source
to build against them.

Owner of this file: **Sushil Raj (team lead)**. Either person can propose a
change, but a change to a field name/type here is a breaking change to the
other person's in-flight work — propose it in chat first, don't just edit
and push. See `CONTRIBUTING.md` rule 3.

Pipeline: `SecurityFinding → AttackHypothesis → ExecutionEvidence → VerificationResult`

```
system/analysis  --SecurityFinding-->  verification/hypothesis
verification/hypothesis  --AttackHypothesis-->  system/sandbox
system/sandbox  --ExecutionEvidence-->  verification/regression
verification/regression  --VerificationResult-->  system/orchestration (CLI output)
```

## 1. `SecurityFinding`
Produced by `system/analysis` (AST/diff parsing). Consumed by `verification/hypothesis`.

| field | type | notes |
|---|---|---|
| `finding_id` | string (uuid) | |
| `file_path` | string | |
| `symbol` | string | function/method name containing the change |
| `diff_hunk` | string | the changed code, unified-diff style |
| `sensitive_op` | enum | `shell_exec`, `subprocess`, `filesystem`, `sql_query`, `deserialization`, `auth_change`, `network_egress` |
| `rationale` | string | why this hunk was flagged |
| `detected_by` | string | rule/analyzer id |
| `severity_hint` | enum | `low`, `medium`, `high` |

## 2. `AttackHypothesis`
Produced by `verification/hypothesis` (LLM + rules). Consumed by `system/sandbox`.

| field | type | notes |
|---|---|---|
| `hypothesis_id` | string (uuid) | |
| `finding_id` | string | FK → `SecurityFinding.finding_id` |
| `security_property` | string | the property claimed to hold, e.g. "no command injection via `cmd`" |
| `attack_vector` | string | human-readable description |
| `payload` | string | the concrete adversarial input/test to execute |
| `expected_if_vulnerable` | string | observable signal proving exploitation |
| `expected_if_safe` | string | observable signal proving the property holds |
| `generated_by` | string | model id + prompt version, for reproducibility |

## 3. `ExecutionEvidence`
Produced by `system/sandbox` (Docker execution). Consumed by `verification/regression`.

| field | type | notes |
|---|---|---|
| `evidence_id` | string (uuid) | |
| `hypothesis_id` | string | FK → `AttackHypothesis.hypothesis_id` |
| `run_id` | string | groups a before/after pair |
| `phase` | enum | `before`, `after` |
| `container_id` | string | |
| `exit_code` | int | |
| `stdout` / `stderr` | string | truncated, size-capped |
| `filesystem_diff` | object | paths touched, created, deleted |
| `network_egress_attempts` | array | should be empty — sandbox is zero-egress |
| `policy_violations` | array | seccomp/docker policy trips, if any |
| `duration_ms` | int | |
| `timestamp` | string (ISO 8601) | |

## 4. `VerificationResult`
Produced by `verification/regression`. Consumed by `system/orchestration` (CLI/dashboard output — the final artifact of the pipeline).

| field | type | notes |
|---|---|---|
| `verdict_id` | string (uuid) | |
| `finding_id` | string | FK |
| `hypothesis_id` | string | FK |
| `before_evidence_id` | string | FK |
| `after_evidence_id` | string | FK |
| `verdict` | enum | `VERIFIED_FIXED`, `STILL_VULNERABLE`, `FALSE_POSITIVE`, `INCONCLUSIVE` |
| `replay_identical` | bool | true only if before/after used the byte-identical payload |
| `confidence` | float 0-1 | |
| `summary` | string | one-line, demo-facing |

`verdict` semantics:
- `VERIFIED_FIXED` — exploit succeeded in `before`, blocked in `after`.
- `STILL_VULNERABLE` — exploit succeeds in both `before` and `after`.
- `FALSE_POSITIVE` — exploit never succeeded in `before` (hypothesis was wrong).
- `INCONCLUSIVE` — sandbox/runtime failure, not a security signal.

## Format

Language-agnostic for now (Markdown spec above is source of truth). Once a
language/stack is picked (see `PLAN.md`), this becomes a JSON Schema and/or
Pydantic models in this same folder — whoever needs it first drafts the
schema file and pings the other before merging, since both sides import it.
