# src/agents/json_parsing.py
"""Shared JSON-from-LLM-response parsing for the Pantheon agents.

Every agent prompts for "Return ONLY valid JSON" and then calls
`json.loads(response)` directly. Real providers (confirmed on Gemini, but
not Gemini-specific) routinely wrap that JSON in a ```json ... ``` markdown
fence anyway, which makes the naive `json.loads` raise every single time,
so every run fell into each agent's own hand-written fallback path
("AI response parsing failed", "Analysis not provided", etc.) -- not because
the provider failed, but because the parser never looked past the fence.

src/agents/observer.py already had a local `extract_json_from_text` helper
doing exactly this (bare-braces regex, then code-fence regex) for its own
parsing. This module is that same two-step extraction, shared so Reasoner,
Actor, Analyzer, Improver and Validator get it too instead of silently
discarding real model output as noise.
"""
import json
import re
from typing import Any, Dict, Optional


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse a dict out of an LLM response that is supposed to be pure JSON.

    Tries, in order: the response as-is, a ```json fenced block, then the
    first bare {...} span. Raises json.JSONDecodeError (with the ORIGINAL
    text as .doc, matching json.loads' own contract) if none of those parse
    to a dict, so existing `except json.JSONDecodeError:` fallback blocks in
    every agent keep working unchanged.
    """
    direct = _try_json(text)
    if isinstance(direct, dict):
        return direct

    fenced = _extract_fenced_json(text)
    if isinstance(fenced, dict):
        return fenced

    braces = _extract_braced_json(text)
    if isinstance(braces, dict):
        return braces

    raise json.JSONDecodeError("No JSON object found in response", text, 0)


def _try_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _extract_fenced_json(text: str) -> Optional[Any]:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        return None
    return _try_json(match.group(1))


def _extract_braced_json(text: str) -> Optional[Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    return _try_json(match.group())
