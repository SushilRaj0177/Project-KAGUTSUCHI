"""Additional command-injection payload variants for the netdiag fixture,
beyond the single payload in the confirmed AttackHypothesis
(see COORDINATION.md's P0 fixture entry).

The confirmed hypothesis's payload (`127.0.0.1; touch ...`) is what
system/sandbox and regression/ are built against and must stay the single
source of truth for the demo's byte-identical replay claim - these are
NOT alternate hypotheses to swap in, just extra proof that `vulnerable()`
is exploitable via more than one shell-metacharacter technique and that
`fixed()` closes all of them, not just the one the demo uses.
"""

from __future__ import annotations

MARKER = "/tmp/kagutsuchi_pwned"

# Each variant chains a marker-creating command onto a legitimate-looking
# host using a different shell metacharacter/technique.
PAYLOAD_VARIANTS: dict[str, str] = {
    "semicolon": f"127.0.0.1; touch {MARKER}",
    "background_and": f"127.0.0.1 && touch {MARKER}",
    "pipe": f"127.0.0.1 | touch {MARKER}",
    "backtick_substitution": f"127.0.0.1`touch {MARKER}`",
    "dollar_paren_substitution": f"127.0.0.1$(touch {MARKER})",
    "newline": f"127.0.0.1\ntouch {MARKER}",
}
