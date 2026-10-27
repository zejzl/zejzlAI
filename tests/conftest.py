"""Shared pytest setup for the zejzlAI smoke suite.

- Runs from the repo root (web_dashboard mounts ./templates and ./static).
- Never reads a local .env: load_dotenv is replaced with a no-op before any
  project module is imported.
- Provider API keys are removed and replaced with dummy values per test.
- Outbound network connections are refused, so a test can never reach a real
  provider, Redis server or webhook.
"""

import os
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import dotenv  # noqa: E402


def _no_dotenv(*args, **kwargs):
    return False


dotenv.load_dotenv = _no_dotenv

PROVIDER_ENV_VARS = [
    "XAI_API_KEY",
    "GROK_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "DEEPSEEK_API_KEY",
    "QWEN_API_KEY",
    "ZAI_API_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_API_KEY",
    "DISCORD_WEBHOOK_URL",
]

_real_connect = socket.socket.connect


def _guarded_connect(self, address):
    if self.family == getattr(socket, "AF_UNIX", None):
        return _real_connect(self, address)
    host = address[0] if isinstance(address, tuple) else address
    if host in ("127.0.0.1", "::1", "localhost"):
        return _real_connect(self, address)
    raise RuntimeError(f"[ERROR] network access blocked in tests: {address!r}")


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch):
    for name in PROVIDER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for name in list(os.environ):
        if name.startswith("ZEJZL_API_KEY_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XAI_API_KEY", "dummy-xai")
    monkeypatch.setenv("GROK_API_KEY", "dummy-grok")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai")
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-gemini")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    yield
