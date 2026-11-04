# tests/test_json_parsing.py
"""parse_json_response: the fix for the actual root cause behind empty/
templated ORAM insights. Reasoner/Actor/Analyzer/Improver/Validator all
called `json.loads(response)` directly despite prompting for "ONLY valid
JSON"; providers (confirmed on Gemini) commonly answer with a ```json
fenced block anyway, so every real response fell straight into each
agent's hand-written fallback path ("AI response parsing failed").
"""
import json

import pytest

from src.agents.json_parsing import parse_json_response, strip_code_fence


def test_parses_plain_json():
    assert parse_json_response('{"a": 1}') == {"a": 1}


def test_parses_json_fenced_with_json_tag():
    text = 'Sure, here you go:\n```json\n{"a": 1, "b": [2, 3]}\n```\nHope that helps.'
    assert parse_json_response(text) == {"a": 1, "b": [2, 3]}


def test_parses_json_fenced_without_tag():
    text = '```\n{"a": 1}\n```'
    assert parse_json_response(text) == {"a": 1}


def test_parses_bare_braces_with_surrounding_prose():
    text = 'The plan is: {"a": 1} -- let me know if you need changes.'
    assert parse_json_response(text) == {"a": 1}


def test_raises_json_decode_error_on_garbage():
    with pytest.raises(json.JSONDecodeError):
        parse_json_response("not json at all, no braces either")


def test_raises_on_non_dict_json():
    # A JSON array or scalar isn't a response object any agent expects.
    with pytest.raises(json.JSONDecodeError):
        parse_json_response("[1, 2, 3]")


def test_strip_code_fence_only_unwraps_a_whole_fenced_response():
    assert strip_code_fence("```toon\na: 1\nb: 2\n```") == "a: 1\nb: 2"
    assert strip_code_fence("```\na: 1\n```\n") == "a: 1"
    assert strip_code_fence("```json\r\n{\"a\": 1}\r\n```") == '{"a": 1}'
    assert strip_code_fence("a: 1") == "a: 1"
    assert strip_code_fence("text ```x``` more") == "text ```x``` more"
    assert strip_code_fence(None) is None
