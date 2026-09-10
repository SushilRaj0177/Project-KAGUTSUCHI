"""
Simple in-memory sliding-window rate limiter for the public endpoints
that cost real money/quota (clone-a-repo, run-a-real-sandboxed-attack,
anything that calls Groq) or write to a third party on the caller's
behalf (opening a PR). Good enough for a single long-running process
(this backend runs on one machine, not distributed serverless) -- no
external store needed.

Keys off X-Client-IP, which the Next.js proxy sets from the real
visitor's x-forwarded-for header (see webapp/lib/clientIp.ts) -- every
request actually reaching this backend otherwise comes from Vercel's own
egress IP, which would make per-IP limiting meaningless.

Two independent windows are layered on the same expensive endpoints:
a short one (rate_limit) stops a tight retry loop or an accidental
double-click storm; a long one (daily_rate_limit) stops one visitor from
quietly burning through this project's entire Groq quota over a day,
which a short window alone doesn't prevent (a slow-and-steady script
sending one request every few seconds would sail under a per-minute cap
all day). Both are per-endpoint, per-IP.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_S = 60.0
_MAX_REQUESTS = 5
_DAILY_WINDOW_S = 86400.0
_DAILY_MAX_REQUESTS = 100

_hits: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    return request.headers.get("x-client-ip") or (request.client.host if request.client else "unknown")


def _check(request: Request, *, window_s: float, max_requests: int, bucket: str) -> None:
    key = f"{bucket}:{request.url.path}:{_client_key(request)}"
    now = time.monotonic()
    window_start = now - window_s

    recent = [t for t in _hits[key] if t > window_start]
    if len(recent) >= max_requests:
        retry_after = int(window_s - (now - recent[0])) + 1
        window_label = f"{int(window_s)}s" if window_s < 3600 else f"{int(window_s / 3600)}h"
        raise HTTPException(
            status_code=429,
            detail=(
                f"Too many requests -- max {max_requests} per {window_label} on this "
                f"endpoint. Try again in {retry_after}s."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    recent.append(now)
    _hits[key] = recent


def rate_limit(request: Request) -> None:
    """FastAPI dependency: raises 429 if this client exceeded
    _MAX_REQUESTS in the last _WINDOW_S seconds on this endpoint. Stops
    a tight retry loop or a double-click storm; pair with
    daily_rate_limit on anything that costs real Groq quota."""
    _check(request, window_s=_WINDOW_S, max_requests=_MAX_REQUESTS, bucket="short")


def daily_rate_limit(request: Request) -> None:
    """FastAPI dependency: raises 429 if this client exceeded
    _DAILY_MAX_REQUESTS in the last _DAILY_WINDOW_S seconds on this
    endpoint. This is the one that actually protects a shared Groq API
    key from one visitor's script quietly burning the whole day's quota
    - a per-minute cap alone doesn't catch a slow, steady stream of
    requests."""
    _check(request, window_s=_DAILY_WINDOW_S, max_requests=_DAILY_MAX_REQUESTS, bucket="daily")
