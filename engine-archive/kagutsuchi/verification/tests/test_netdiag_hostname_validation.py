"""Edge-case coverage for fixed()'s hostname allowlist: common shell
metacharacter payloads must be rejected outright (ValueError), not just
happen to be inert once they reach subprocess's argv-list exec."""

from __future__ import annotations

import pytest

from verification.fixtures.netdiag import _HOSTNAME_RE, fixed

INJECTION_PAYLOADS = [
    "127.0.0.1; touch /tmp/kagutsuchi_pwned",
    "127.0.0.1 && touch /tmp/kagutsuchi_pwned",
    "127.0.0.1 | touch /tmp/kagutsuchi_pwned",
    "127.0.0.1`touch /tmp/kagutsuchi_pwned`",
    "127.0.0.1$(touch /tmp/kagutsuchi_pwned)",
    "",
    "   ",
    "-rf /",  # looks like a flag, not a host
]

VALID_HOSTS = [
    "127.0.0.1",
    "localhost",
    "example.com",
    "sub.example-01.com",
]


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_fixed_rejects_metacharacter_payloads(payload):
    with pytest.raises(ValueError):
        fixed(payload)


@pytest.mark.parametrize("host", VALID_HOSTS)
def test_hostname_regex_accepts_legitimate_hosts(host):
    assert _HOSTNAME_RE.match(host)


def test_hostname_regex_rejects_trailing_shell_metacharacter():
    assert not _HOSTNAME_RE.match("127.0.0.1;")
    assert not _HOSTNAME_RE.match("127.0.0.1 ")
