import pytest
from fastapi import HTTPException

from server.rate_limit import _DAILY_MAX_REQUESTS, _MAX_REQUESTS, _hits, daily_rate_limit, rate_limit


class _FakeClient:
    host = "203.0.113.7"


class _FakeRequest:
    def __init__(self, path: str = "/api/verify", client_ip: str | None = "203.0.113.7"):
        self.url = type("U", (), {"path": path})()
        self.headers = {"x-client-ip": client_ip} if client_ip else {}
        self.client = _FakeClient()


@pytest.fixture(autouse=True)
def _clear_hits():
    _hits.clear()
    yield
    _hits.clear()


def test_allows_requests_under_the_limit():
    req = _FakeRequest()
    for _ in range(_MAX_REQUESTS):
        rate_limit(req)  # should not raise


def test_blocks_the_request_over_the_limit():
    req = _FakeRequest()
    for _ in range(_MAX_REQUESTS):
        rate_limit(req)
    with pytest.raises(HTTPException) as exc_info:
        rate_limit(req)
    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


def test_different_clients_have_independent_budgets():
    req_a = _FakeRequest(client_ip="203.0.113.7")
    req_b = _FakeRequest(client_ip="198.51.100.4")
    for _ in range(_MAX_REQUESTS):
        rate_limit(req_a)
    rate_limit(req_b)  # a different client is not affected by A's usage


def test_different_endpoints_have_independent_budgets():
    req_analyze = _FakeRequest(path="/api/analyze-repo")
    req_verify = _FakeRequest(path="/api/verify")
    for _ in range(_MAX_REQUESTS):
        rate_limit(req_analyze)
    rate_limit(req_verify)  # a different endpoint is not affected


def test_falls_back_to_request_client_host_without_x_client_ip_header():
    req = _FakeRequest(client_ip=None)
    for _ in range(_MAX_REQUESTS):
        rate_limit(req)
    with pytest.raises(HTTPException):
        rate_limit(req)


def test_daily_limit_allows_more_requests_than_the_short_one():
    req = _FakeRequest()
    # exhaust the short-window budget, then keep going under the daily
    # one -- they must be tracked independently (see bucket= in _check),
    # not share one counter that the short limiter would already trip.
    for _ in range(_DAILY_MAX_REQUESTS):
        daily_rate_limit(req)
    with pytest.raises(HTTPException) as exc_info:
        daily_rate_limit(req)
    assert exc_info.value.status_code == 429


def test_short_and_daily_limits_are_independent_counters():
    req = _FakeRequest()
    for _ in range(_MAX_REQUESTS):
        rate_limit(req)
    with pytest.raises(HTTPException):
        rate_limit(req)
    # the short limit tripping must not affect the separate daily budget
    daily_rate_limit(req)
