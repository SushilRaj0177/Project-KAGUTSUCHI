"""
In-memory background job tracking for slow endpoints - re-platformed
near-verbatim from `engine-archive/kagutsuchi/server/jobs.py`, which
already exists because of a real production problem: scanning a repo
(clone + full measurement pipeline) can take longer than a typical
serverless proxy's request timeout (~60s on Vercel), which caused a live
504 in the original product. Making the slow work a background job means
the initial request returns almost instantly with a job id, and the
caller polls for the result instead of holding one request open past the
gateway's timeout.

A plain in-memory dict plus a background thread is enough for a single
always-on process (not serverless) - no external queue or DB needed.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

# Finished jobs are kept around long enough for a slow poller to still see
# the result, then garbage-collected so this dict can't grow forever on a
# long-running process.
_JOB_TTL_S = 900.0


@dataclass
class Job:
    id: str
    status: str = "running"  # "running" | "done" | "error"
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.monotonic)


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def _gc_stale_jobs() -> None:
    cutoff = time.monotonic() - _JOB_TTL_S
    with _lock:
        for job_id in [jid for jid, job in _jobs.items() if job.created_at < cutoff]:
            del _jobs[job_id]


def start_job(fn: Callable[[], Any]) -> str:
    """Runs `fn` in a background thread and returns a job id immediately.
    `fn` takes no arguments - callers should close over whatever it needs.
    Any exception `fn` raises is captured, not propagated (there's no
    caller left waiting synchronously to catch it) - it's surfaced to
    whoever later polls get_job()."""
    _gc_stale_jobs()
    job = Job(id=str(uuid.uuid4()))
    with _lock:
        _jobs[job.id] = job

    def _run() -> None:
        try:
            job.result = fn()
            job.status = "done"
        except Exception as exc:  # noqa: BLE001 - must never crash this thread silently; the poller needs to see *some* outcome
            job.error = str(exc)
            job.status = "error"

    threading.Thread(target=_run, daemon=True).start()
    return job.id


def get_job(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)
