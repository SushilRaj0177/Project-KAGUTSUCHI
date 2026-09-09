"""
Kagutsuchi CLI — the canonical interface. If the dashboard fails, this
still runs the full loop and prints a verdict.
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from contracts import AttackHypothesis
from system.analysis import scan_diff, scan_source
from system.orchestration import new_run_id, replay_attack, run_attack
from system.sandbox.docker_runner import SandboxUnavailableError

app = typer.Typer(help="Kagutsuchi — autonomous code integrity verification.")


@app.command()
def analyze(file: Path) -> None:
    """Scan a Python file for sensitive operations and print SecurityFindings."""
    findings = scan_source(file.read_text(), str(file))
    if not findings:
        typer.echo("No sensitive operations found.")
        raise typer.Exit()
    for f in findings:
        typer.echo(f.model_dump_json(indent=2))


@app.command()
def analyze_diff(old_file: Path, new_file: Path) -> None:
    """Scan only the functions that changed between old_file and new_file
    — the actual 'detect' step against a real commit, not a whole-file scan."""
    findings = scan_diff(old_file.read_text(), new_file.read_text(), str(new_file))
    if not findings:
        typer.echo("No sensitive operations in the changed functions.")
        raise typer.Exit()
    for f in findings:
        typer.echo(f.model_dump_json(indent=2))


@app.command()
def verify(
    vulnerable_file: Path,
    fixed_file: Path,
    payload: str = typer.Option(..., help="Attack payload to run before and after."),
) -> None:
    """Run one payload against a vulnerable/fixed pair and print raw
    before/after evidence.

    This is a standalone harness for testing system/sandbox before
    verification/hypothesis and verification/regression exist — the real
    payload comes from an AttackHypothesis, and the real verdict comes
    from verification/regression comparing the two evidence objects this
    prints.
    """
    hypothesis = AttackHypothesis(
        finding_id="manual-test",
        security_property="manual CLI test — not LLM-generated",
        attack_vector="manual",
        payload=payload,
        expected_if_vulnerable="attack payload executes/succeeds",
        expected_if_safe="attack payload is neutralized",
        generated_by="manual-cli",
    )
    run_id = new_run_id()

    try:
        before = run_attack(
            vulnerable_code=vulnerable_file.read_text(), hypothesis=hypothesis, run_id=run_id
        )
        after = replay_attack(
            fixed_code=fixed_file.read_text(), hypothesis=hypothesis, run_id=run_id
        )
    except SandboxUnavailableError as exc:
        typer.echo(f"Sandbox unavailable: {exc}", err=True)
        raise typer.Exit(code=2)

    typer.echo(json.dumps({"before": before.model_dump(), "after": after.model_dump()}, indent=2))


if __name__ == "__main__":
    app()
