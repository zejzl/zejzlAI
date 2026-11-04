# tests/test_provider_defaults.py
"""ORAM_DEFAULT_PROVIDER: the one knob that used to be six hardcoded "grok"
literals across the Pantheon agents (Observer/Reasoner/Actor/Analyzer/
Improver/Validator). Lets the whole run loop point at a different provider
(e.g. Gemini, when there's a subscription but no pay-as-you-go Grok/xAI
tokens) without touching agent code.
"""
from src.agents.provider_defaults import default_provider_name


def test_defaults_to_grok_when_unset(monkeypatch):
    monkeypatch.delenv("ORAM_DEFAULT_PROVIDER", raising=False)
    assert default_provider_name() == "grok"


def test_reads_the_env_var_when_set(monkeypatch):
    monkeypatch.setenv("ORAM_DEFAULT_PROVIDER", "gemini")
    assert default_provider_name() == "gemini"


def test_blank_value_falls_back_to_grok(monkeypatch):
    monkeypatch.setenv("ORAM_DEFAULT_PROVIDER", "")
    assert default_provider_name() == "grok"
