# src/agents/provider_defaults.py
"""Shared default-provider lookup for the Pantheon agents.

Each agent (Actor, Analyzer, Improver, Observer, Reasoner, Validator) falls
back to this when the caller doesn't name a provider explicitly. It used to
be a literal "grok" in every file; this makes the fallback one env var
(ORAM_DEFAULT_PROVIDER) instead of six hardcoded strings, so switching the
whole Pantheon run loop to a different provider (e.g. Gemini, when there is
a subscription but no pay-as-you-go Grok/xAI tokens) is a one-line .env
change rather than a code change.
"""
import os

_FALLBACK = "grok"


def default_provider_name() -> str:
    """The provider to use when nothing more specific was asked for.

    Reads ORAM_DEFAULT_PROVIDER at call time (not import time) so tests can
    monkeypatch the environment per-test without reloading modules. Falls
    back to "grok" to keep existing behavior for anyone who hasn't set it.
    """
    return os.environ.get("ORAM_DEFAULT_PROVIDER", _FALLBACK) or _FALLBACK
