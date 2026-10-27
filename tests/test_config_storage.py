"""Saved provider config: round-trips, and never stores API keys."""

import asyncio

import ai_framework
from src.multimodal_ai import GPT4VisionProvider


def _config():
    return {
        "providers": {
            "claude": {"api_key": "secret-claude", "model": "claude-sonnet-5-5"},
            "grok": {"api_key": "secret-grok", "model": "grok-4.3"},
        },
        "default_provider": "claude",
    }


def test_storage_drops_api_keys_and_keeps_the_rest():
    raw = ai_framework.config_to_storage(_config())
    assert "secret" not in raw
    assert "claude-sonnet-5-5" in raw and "default_provider" in raw


def test_storage_does_not_modify_the_callers_config():
    config = _config()
    ai_framework.config_to_storage(config)
    assert config["providers"]["claude"]["api_key"] == "secret-claude"


def test_load_fills_keys_from_defaults():
    raw = ai_framework.config_to_storage(_config())
    defaults = {"providers": {"claude": {"api_key": "from-env"}}}
    loaded = ai_framework.config_from_storage(raw, defaults)
    assert loaded["providers"]["claude"]["api_key"] == "from-env"
    assert loaded["providers"]["grok"]["api_key"] == ""
    assert loaded["providers"]["claude"]["model"] == "claude-sonnet-5-5"


def test_sqlite_config_round_trip_without_keys_on_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-claude")

    async def scenario():
        store = ai_framework.SQLitePersistence(db_path=str(tmp_path / "test.db"))
        store.config_path = tmp_path / "config.json"
        await store.initialize()
        try:
            await store.save_config(_config())
            return store.config_path.read_text(), await store.load_config()
        finally:
            await store.cleanup()

    on_disk, loaded = asyncio.run(scenario())
    assert "secret" not in on_disk
    assert loaded["providers"]["claude"]["api_key"] == "env-claude"
    assert loaded["default_provider"] == "claude"


def test_vision_provider_uses_current_model():
    provider = GPT4VisionProvider(api_key="test-key")
    assert provider.model == "gpt-5-mini"
    assert provider.default_model == "gpt-5-mini"
