"""Decision gate tests. The HTTP call is mocked; CI never needs Ollama.

The last test runs against a real local Ollama only when one answers on
127.0.0.1:11434 and ZEJZLAI_TEST_LOCAL_GATE=1 is set.
"""

import asyncio
import os
import socket
import urllib.request

import pytest

from src import decision_gate as dg
from src.decision_gate import DecisionGate, NonLocalURLError


def _response(choice, probs):
    return {
        "model": "clef-flash",
        "answers": {"size": {"type": "choice", "choice": choice,
                             "probabilities": probs, "confidence": max(probs.values())}},
    }


def _gate(**kwargs):
    kwargs.setdefault("enabled", True)
    return DecisionGate(**kwargs)


def _mock_post(monkeypatch, gate, result=None, exc=None, delay=0.0, calls=None):
    async def fake_post(payload):
        if calls is not None:
            calls.append(payload)
        if delay:
            await asyncio.sleep(delay)
        if exc is not None:
            raise exc
        return result

    monkeypatch.setattr(gate, "_post", fake_post)


ALL = ["chatgpt", "claude", "gemini", "grok"]


def test_high_confidence_routes_to_mapped_provider(monkeypatch):
    gate = _gate()
    calls = []
    _mock_post(monkeypatch, gate, _response("large", {"small": 0.02, "medium": 0.08, "large": 0.9}),
               calls=calls)
    assert asyncio.run(gate.route("write a compiler", ALL)) == "claude"
    assert calls[0]["model"] == "clef-flash"
    assert calls[0]["questions"]["size"]["type"] == "choice"

    decision = asyncio.run(gate.classify("write a compiler"))
    assert decision.tier == "large"
    assert decision.probability == pytest.approx(0.9)
    assert decision.latency_ms >= 0


def test_custom_tier_mapping(monkeypatch):
    gate = _gate(tiers=dg.parse_tiers("small=chatgpt"))
    _mock_post(monkeypatch, gate, _response("small", {"small": 0.95, "medium": 0.04, "large": 0.01}))
    assert asyncio.run(gate.route("2+2", ALL)) == "chatgpt"
    assert gate.tiers["large"] == "claude"


def test_low_confidence_falls_back(monkeypatch):
    gate = _gate(threshold=0.7)
    _mock_post(monkeypatch, gate, _response("medium", {"small": 0.3, "medium": 0.5, "large": 0.2}))
    assert asyncio.run(gate.classify("hmm")) is None
    assert asyncio.run(gate.route("hmm", ALL)) is None


def test_unregistered_provider_falls_back(monkeypatch):
    gate = _gate()
    _mock_post(monkeypatch, gate, _response("large", {"small": 0.0, "medium": 0.1, "large": 0.9}))
    assert asyncio.run(gate.route("big job", ["chatgpt", "gemini"])) is None


def test_bad_response_shape_fails_open(monkeypatch):
    gate = _gate()
    _mock_post(monkeypatch, gate, {"error": "model not found"})
    assert asyncio.run(gate.route("x", ALL)) is None


@pytest.mark.parametrize("exc", [ConnectionRefusedError(), OSError("boom"), RuntimeError("x")])
def test_errors_fail_open(monkeypatch, exc):
    gate = _gate()
    _mock_post(monkeypatch, gate, exc=exc)
    assert asyncio.run(gate.route("x", ALL)) is None


def test_timeout_fails_open(monkeypatch):
    gate = _gate(timeout=0.05)
    _mock_post(monkeypatch, gate, _response("small", {"small": 1.0}), delay=2.0)
    assert asyncio.run(gate.route("x", ALL)) is None


def test_real_connection_refused_fails_open():
    # Find a free local port, close it, and point the real aiohttp client at it.
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    gate = _gate(base_url=f"http://127.0.0.1:{port}", timeout=0.5)
    assert asyncio.run(gate.route("x", ALL)) is None


def test_flag_off_makes_no_call(monkeypatch):
    gate = DecisionGate.from_env({})
    assert gate.enabled is False
    calls = []
    _mock_post(monkeypatch, gate, _response("small", {"small": 1.0}), calls=calls)
    assert asyncio.run(gate.route("x", ALL)) is None
    assert calls == []


def test_from_env_reads_settings():
    gate = DecisionGate.from_env({
        "ZEJZLAI_DECISION_GATE": "1",
        "ZEJZLAI_DECISION_GATE_URL": "http://localhost:9999/",
        "ZEJZLAI_DECISION_GATE_MODEL": "clef",
        "ZEJZLAI_DECISION_GATE_TIMEOUT": "0.5",
        "ZEJZLAI_DECISION_GATE_THRESHOLD": "0.8",
        "ZEJZLAI_DECISION_GATE_TIERS": "medium=chatgpt, bogus=x",
    })
    assert gate.enabled
    assert gate.base_url == "http://localhost:9999"
    assert gate.model == "clef"
    assert gate.timeout == 0.5
    assert gate.threshold == 0.8
    assert gate.tiers == {"small": "gemini", "medium": "chatgpt", "large": "claude"}


@pytest.mark.parametrize("url", ["https://api.example.com", "http://10.0.0.5:11434",
                                 "http://192.168.1.2:11434", "http://localhost.evil.com"])
def test_non_local_url_rejected(url):
    with pytest.raises(NonLocalURLError):
        DecisionGate(enabled=True, base_url=url)
    gate = DecisionGate.from_env({"ZEJZLAI_DECISION_GATE": "1", "ZEJZLAI_DECISION_GATE_URL": url})
    assert gate.enabled is False


@pytest.mark.parametrize("url", ["http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434"])
def test_local_urls_accepted(url):
    assert DecisionGate(enabled=True, base_url=url).base_url == url


def test_non_local_url_allowed_with_opt_in():
    gate = DecisionGate.from_env({"ZEJZLAI_DECISION_GATE": "1",
                                  "ZEJZLAI_DECISION_GATE_URL": "http://10.0.0.5:11434",
                                  "ZEJZLAI_DECISION_GATE_ALLOW_REMOTE": "1"})
    assert gate.enabled and gate.base_url == "http://10.0.0.5:11434"


def test_logs_do_not_contain_message(monkeypatch, caplog):
    gate = _gate()
    _mock_post(monkeypatch, gate, _response("small", {"small": 0.99, "medium": 0.01, "large": 0.0}))
    secret = "my private question about xyzzy"
    with caplog.at_level("INFO", logger="DecisionGate"):
        assert asyncio.run(gate.route(secret, ALL)) == "gemini"
    assert "provider=gemini" in caplog.text
    assert "xyzzy" not in caplog.text


def test_message_bus_uses_gate_only_when_enabled(monkeypatch):
    import ai_framework

    monkeypatch.delenv("ZEJZLAI_DECISION_GATE", raising=False)
    bus = ai_framework.AsyncMessageBus()
    assert bus.decision_gate.enabled is False
    assert asyncio.run(bus._route_with_decision_gate("x")) is None

    bus.providers = {name: object() for name in ALL}
    bus.decision_gate = _gate()
    _mock_post(monkeypatch, bus.decision_gate,
               _response("medium", {"small": 0.1, "medium": 0.85, "large": 0.05}))
    assert asyncio.run(bus._route_with_decision_gate("summarise this")) == "grok"


def _local_ollama_up():
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=0.5):
            return True
    except Exception:
        return False


@pytest.mark.skipif(os.environ.get("ZEJZLAI_TEST_LOCAL_GATE") != "1" or not _local_ollama_up(),
                    reason="set ZEJZLAI_TEST_LOCAL_GATE=1 with a local Ollama + clef-flash")
def test_real_local_clef():
    gate = DecisionGate(enabled=True, timeout=30.0, threshold=0.0)
    small = asyncio.run(gate.classify("What is 2+2?"))
    large = asyncio.run(gate.classify(
        "Write a compiler for a C subset targeting x86-64 with register allocation."))
    assert small is not None and small.tier == "small"
    assert large is not None and large.tier == "large"
