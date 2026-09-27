"""Second P0 fixture: a real SQL-injection sink, to prove the pipeline
generalizes beyond netdiag.py's command injection (see COORDINATION.md's
"Next milestone: prove this generalizes beyond one fixture").

`vulnerable()` builds a SQL script by string-interpolating untrusted
input into `executescript()`, so a `'; ...; --` payload chains arbitrary
extra SQL statements onto the intended SELECT - the classic auth-bypass/
data-exfil injection class (`system/analysis`'s `sql_query` sensitive_op).
`fixed()` uses a single parameterized `execute()` call instead, so the
same payload is bound as an inert literal search value.

Uses the SAME observable proof as netdiag.py (the "/tmp/kagutsuchi_pwned"
marker file being created) via SQLite's `ATTACH DATABASE` - this is
deliberate: it lets `verification/regression/verify.py`'s existing,
netdiag-built `_marker_created()` check work completely unmodified. The
attack chains `ATTACH DATABASE '/tmp/kagutsuchi_pwned' AS pwn; CREATE
TABLE pwn.t(x);` onto the query, which creates that exact file on disk -
proof of arbitrary SQL execution, not just data disclosure.
"""

from __future__ import annotations

import sqlite3


def _seed(cursor: sqlite3.Cursor) -> None:
    cursor.execute("CREATE TABLE users (name TEXT)")
    cursor.execute("INSERT INTO users VALUES ('alice')")


def vulnerable(name: str) -> int:
    """SQL injection: `name` is string-interpolated into executescript(),
    so a `'; ...; --` payload runs as additional, attacker-controlled SQL
    statements rather than being treated as a literal search value."""
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    _seed(cur)
    cur.executescript(f"SELECT * FROM users WHERE name = '{name}'")
    con.commit()
    return 0


def fixed(name: str) -> int:
    """Safe: a single parameterized query via execute() - no string
    interpolation and no executescript, so injected SQL is bound as an
    inert literal value and never parsed as additional statements."""
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    _seed(cur)
    cur.execute("SELECT * FROM users WHERE name = ?", (name,))
    return len(cur.fetchall())
