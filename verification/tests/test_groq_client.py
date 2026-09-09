"""generate_hypothesis_json() must turn every Groq-side failure mode into
GroqUnavailable - never let a raw exception (bad JSON, network error,
unexpected response shape) escape to the caller."""

from __future__ import annotations

import pytest

import verification.hypothesis.groq_client as groq_client
from verification.hypothesis.groq_client import GroqUnavailable, generate_hypothesis_json


class _FakeChoice:
    def __init__(self, content: str):
        self.message = type("Msg", (), {"content": content})()


class _FakeCompletion:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeChatCompletions:
    def __init__(self, content: str):
        self._content = content

    def create(self, **kwargs):
        return _FakeCompletion(self._content)


class _FakeChat:
    def __init__(self, content: str):
        self.completions = _FakeChatCompletions(content)


class _FakeGroqClient:
    def __init__(self, content: str, **kwargs):
        self.chat = _FakeChat(content)


def _patch_groq(monkeypatch, content: str):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-test")
    monkeypatch.setattr(groq_client, "Groq", lambda **kw: _FakeGroqClient(content))


def test_malformed_json_raises_groq_unavailable(monkeypatch):
    _patch_groq(monkeypatch, "this is not json at all {")
    with pytest.raises(GroqUnavailable):
        generate_hypothesis_json("irrelevant prompt")


def test_valid_json_non_object_still_parses_but_caller_must_handle_shape(monkeypatch):
    # A JSON array is valid JSON but not the dict shape callers expect -
    # generate_hypothesis_json itself doesn't enforce shape, only valid JSON.
    _patch_groq(monkeypatch, "[1, 2, 3]")
    result = generate_hypothesis_json("irrelevant prompt")
    assert result == [1, 2, 3]


def test_missing_api_key_raises_groq_unavailable(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(GroqUnavailable):
        generate_hypothesis_json("irrelevant prompt")


def test_valid_json_object_parses_normally(monkeypatch):
    _patch_groq(monkeypatch, '{"security_property": "no injection", "payload": "x"}')
    result = generate_hypothesis_json("irrelevant prompt")
    assert result == {"security_property": "no injection", "payload": "x"}
