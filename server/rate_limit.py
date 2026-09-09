"""
Simple in-memory sliding-window rate limiter for the two expensive public
endpoints (clone-a-repo, run-a-real-sandboxed-attack). Good enough for a
single long-running process (this backend runs on one machine, not
distributed serverless) -- no external store needed.

Keys off X-Client-IP, which the Next.js proxy sets from the real
visitor's x-forwarded-for header (see webapp/lib/clientIp.ts) -- every
request actually reaching this backend otherwise comes from Vercel's own
egress IP, which would make per-IP limiting meaningless.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_S = 60.0
_MAX_REQUESTS = 5

_hits: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    return request.headers.get("x-client-ip") or (request.client.host if request.client else "unknown")


def rate_limit(request: Request) -> None:
    """FastAPI dependency: raises 429 if this client exceeded
    _MAX_REQUESTS in the last _WINDOW_S seconds. Call per-endpoint so
    different endpoints get independent budgets."""
    key = f"{request.url.path}:{_client_key(request)}"
    now = time.monotonic()
    window_start = now - _WINDOW_S

    recent = [t for t in _hits[key] if t > window_start]
    if len(recent) >= _MAX_REQUESTS:
        retry_after = int(_WINDOW_S - (now - recent[0])) + 1
        raise HTTPException(
            status_code=429,
            detail=(
                f"Too many requests -- max {_MAX_REQUESTS} per {int(_WINDOW_S)}s on this "
                f"endpoint. Try again in {retry_after}s."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    recent.append(now)
    _hits[key] = recent
