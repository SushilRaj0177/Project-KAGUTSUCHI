"""Thin Groq (OpenAI-compatible) client wrapper for hypothesis generation.

No Anthropic/Claude calls here by design (see PLAN.md - zero-cost hackathon
build). API key is read from the GROQ_API_KEY environment variable only -
never hardcode it. Load it from a local, gitignored .env via python-dotenv
before calling anything here.
"""

from __future__ import annotations

import json
import os
import time

from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"


class GroqUnavailable(Exception):
    """Raised when the Groq API can't be reached or is rate-limited."""


_REQUEST_TIMEOUT_S = 20.0

# One malformed-JSON generation is a real occurrence, not exceptional -
# Groq's json_object mode validates the model's own output and returns a
# 400 if the model failed to produce valid JSON (seen in practice on
# payloads that have to embed raw-ish bytes, like a base64 pickle stream,
# as a JSON string). A single failure here used to mean "give up" even
# though the exact same prompt often succeeds on a second try. Retrying
# with a nudged-up temperature (0 is near-greedy/repeatable, so retrying
# at the identical temperature would likely just fail the identical way
# again) meaningfully improves the odds without the caller ever seeing
# the transient failure.
_MAX_ATTEMPTS = 3
_RETRY_TEMPERATURES = [0, 0.4, 0.7]
_RETRY_BACKOFF_S = 1.0


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqUnavailable("GROQ_API_KEY is not set")
    # Bound the worst case explicitly - a slow/hanging Groq call (rather
    # than a clean failure) shouldn't be able to blow a caller's own
    # gateway/function timeout (see COORDINATION.md's repo-scan 504 note:
    # server/repo_scan.py runs several of these concurrently and needs
    # each one capped, not just retried on outright failure).
    return Groq(api_key=api_key, timeout=_REQUEST_TIMEOUT_S)


def generate_hypothesis_json(prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """Call Groq and parse a JSON object out of the response.

    Retries automatically (up to _MAX_ATTEMPTS, nudging temperature up
    each time) on a transient/malformed-generation failure, since the
    same prompt often succeeds on a second attempt. Raises
    GroqUnavailable only once every attempt has failed (auth failure
    never retries - a missing/invalid key won't fix itself) so callers
    can fall back to a hardcoded hypothesis instead of crashing the demo.
    """
    client = _client()  # raises immediately on a missing key - no point retrying that

    last_exc: Exception | None = None
    for attempt, temperature in enumerate(_RETRY_TEMPERATURES[:_MAX_ATTEMPTS]):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            return json.loads(content)
        except Exception as exc:  # noqa: BLE001 - any failure retries, then degrades to fallback
            last_exc = exc
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_RETRY_BACKOFF_S)

    raise GroqUnavailable(str(last_exc)) from last_exc
