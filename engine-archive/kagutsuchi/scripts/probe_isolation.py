#!/usr/bin/env python3
"""
Run this ON RENDER (or wherever the backend is actually deployed) to get
a real, authoritative answer to: can this specific host build a bespoke
namespace/cgroup-based sandbox runtime, or does it hit the same wall
Docker-in-Docker already hit here?

How to run it on Render:
  - If your plan has Shell access (Render dashboard -> your service ->
    Shell tab): `PYTHONPATH=. python scripts/probe_isolation.py`
  - Otherwise: temporarily add this as a one-off Render Job, or curl the
    /api/debug/isolation-probe endpoint added to server/main.py for the
    same result over HTTP (remove that route once you have your answer -
    it's a diagnostic, not a permanent feature).

Every check here is side-effect-free by design (see
system/sandbox/isolation_probe.py's docstring) - safe to run against a
live service.
"""
from __future__ import annotations

import json
import sys

from system.sandbox.isolation_probe import run_isolation_probe


def main() -> None:
    report = run_isolation_probe()
    result = report.as_dict()
    print(json.dumps(result, indent=2))
    print()
    if result["all_ok"]:
        print("VERDICT: this host CAN build a bespoke isolated runtime here.")
        sys.exit(0)
    else:
        print(
            "VERDICT: this host CANNOT build a bespoke isolated runtime here - "
            "at least one required primitive is blocked, for the same class of "
            "reason Docker-in-Docker doesn't work here either. A bespoke runtime "
            "would not get you real isolation on this host."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
