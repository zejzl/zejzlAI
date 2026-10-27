"""Provider defaults and response parsing with current models (thinking parts, refusals)."""

import asyncio

import pytest

import ai_framework


class _FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload

    async def text(self):
        return str(self._payload)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.sent = None

    def post(self, url, json):
        self.sent = json
        return _FakeResponse(self.status, self.payload)


def _provider(payload):
    provider = ai_framework.ClaudeProvider(api_key="test-key")
    provider.session = _FakeSession(payload)
    return provider


def test_defaults_to_current_sonnet():
    assert ai_framework.ClaudeProvider(api_key="test-key").default_model == "claude-sonnet-5-5"


def test_joins_text_blocks_after_a_thinking_block():
    provider = _provider({
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig"},
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": " world"},
        ],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 3, "output_tokens": 5},
    })
    text, usage = asyncio.run(provider.generate_response("hi"))
    assert text == "Hello world"
    assert usage.completion_tokens == 5
    assert provider.session.sent["max_tokens"] >= 16000


def test_refusal_raises():
    provider = _provider({
        "content": [],
        "stop_reason": "refusal",
        "stop_details": {"type": "refusal", "category": "cyber"},
        "usage": {},
    })
    with pytest.raises(Exception, match="declined"):
        asyncio.run(provider.generate_response("hi"))


def test_gemini_skips_thought_parts():
    provider = ai_framework.GeminiProvider(api_key="test-key")
    provider.session = _FakeSession({
        "candidates": [{"content": {"parts": [
            {"text": "planning...", "thought": True},
            {"text": "Answer"},
        ]}}],
        "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 1},
    })
    text, _ = asyncio.run(provider.generate_response("hi"))
    assert text == "Answer"
    assert provider.default_model == "gemini-3.5-flash-lite"


def test_grok_default_is_current():
    assert ai_framework.GrokProvider(api_key="test-key").default_model == "grok-4.3"
