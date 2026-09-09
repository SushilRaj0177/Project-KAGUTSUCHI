"""Thin Groq (OpenAI-compatible) client wrapper for hypothesis generation.

No Anthropic/Claude calls here by design (see PLAN.md - zero-cost hackathon
build). API key is read from the GROQ_API_KEY environment variable only -
never hardcode it. Load it from a local, gitignored .env via python-dotenv
before calling anything here.
"""

from __future__ import annotations

import json
import os

from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"


class GroqUnavailable(Exception):
    """Raised when the Groq API can't be reached or is rate-limited."""


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqUnavailable("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def generate_hypothesis_json(prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """Call Groq and parse a JSON object out of the response.

    Raises GroqUnavailable on any failure (auth, network, rate limit,
    malformed response) so callers can fall back to a hardcoded hypothesis
    instead of crashing the demo.
    """
    try:
        client = _client()
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        return json.loads(content)
    except Exception as exc:  # noqa: BLE001 - any failure degrades to fallback
        raise GroqUnavailable(str(exc)) from exc
