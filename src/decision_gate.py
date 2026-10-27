"""Local decision gate: pick a provider tier with a System One model.

The gate asks a local decision model (Clef via Ollama's /v1/systemone
endpoint, Jev-API compatible) which model size a message needs, then maps the
answer (small / medium / large) to a registered provider.

Design rules:
- Off by default. Enable with ZEJZLAI_DECISION_GATE=1.
- Local only. The base URL must point at localhost unless
  ZEJZLAI_DECISION_GATE_ALLOW_REMOTE=1 is set, so message text never leaves
  the machine by accident.
- Fail open. Any error, timeout or low-confidence answer returns None and the
  caller keeps its normal default provider.
- No message content in logs, only its length and a short hash.

Environment variables:
    ZEJZLAI_DECISION_GATE               1/true/yes/on to enable (default off)
    ZEJZLAI_DECISION_GATE_URL           base URL (default http://127.0.0.1:11434)
    ZEJZLAI_DECISION_GATE_MODEL         model name (default clef-flash)
    ZEJZLAI_DECISION_GATE_TIMEOUT       seconds (default 1.0)
    ZEJZLAI_DECISION_GATE_THRESHOLD     min probability, 0..1 (default 0.7)
    ZEJZLAI_DECISION_GATE_TIERS         e.g. "small=gemini,medium=grok,large=claude"
    ZEJZLAI_DECISION_GATE_ALLOW_REMOTE  1 to allow a non-local base URL
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger("DecisionGate")

ENDPOINT = "/v1/systemone"
DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "clef-flash"
DEFAULT_TIMEOUT = 1.0
DEFAULT_THRESHOLD = 0.7
DEFAULT_TIERS: Dict[str, str] = {
    "small": "gemini",
    "medium": "grok",
    "large": "claude",
}
TIERS = ("small", "medium", "large")
MAX_STATE_CHARS = 4000

SIZE_QUESTION: Dict[str, Any] = {
    "type": "choice",
    "instructions": "Which model size is needed to answer this request well?",
    "criteria": {
        "small": "Trivial lookup, short factual answer, greeting or simple arithmetic.",
        "medium": "Moderate reasoning, summarising, everyday writing or small code edits.",
        "large": "Complex multi-step engineering, long code, deep analysis or careful reasoning.",
    },
}

_TRUE = {"1", "true", "yes", "on"}


class NonLocalURLError(ValueError):
    """Raised when the gate is pointed at a non-local host without opt-in."""


@dataclass
class GateDecision:
    tier: str
    probability: float
    latency_ms: float
    provider: Optional[str] = None
    probabilities: Dict[str, float] = field(default_factory=dict)


def _flag(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in _TRUE


def is_local_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def parse_tiers(spec: Optional[str]) -> Dict[str, str]:
    """Parse "small=gemini,medium=grok" into a dict merged over the defaults."""
    tiers = dict(DEFAULT_TIERS)
    for part in (spec or "").split(","):
        if "=" not in part:
            continue
        tier, provider = (s.strip().lower() for s in part.split("=", 1))
        if tier in TIERS and provider:
            tiers[tier] = provider
    return tiers


def content_fingerprint(content: str) -> str:
    """Length and short hash, safe to log."""
    digest = hashlib.sha256(content.encode("utf-8", "replace")).hexdigest()[:10]
    return f"len={len(content)} sha={digest}"


class DecisionGate:
    """Async client for a local System One decision model."""

    def __init__(self, enabled: bool = False, base_url: str = DEFAULT_BASE_URL,
                 model: str = DEFAULT_MODEL, timeout: float = DEFAULT_TIMEOUT,
                 threshold: float = DEFAULT_THRESHOLD,
                 tiers: Optional[Mapping[str, str]] = None,
                 allow_remote: bool = False):
        base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        if not allow_remote and not is_local_url(base_url):
            raise NonLocalURLError(
                f"decision gate URL must be local (got host {urlparse(base_url).hostname!r}); "
                "set ZEJZLAI_DECISION_GATE_ALLOW_REMOTE=1 to override")
        self.enabled = bool(enabled)
        self.base_url = base_url
        self.model = model or DEFAULT_MODEL
        self.timeout = float(timeout)
        self.threshold = float(threshold)
        self.tiers = dict(tiers) if tiers else dict(DEFAULT_TIERS)

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "DecisionGate":
        env = os.environ if env is None else env
        enabled = _flag(env.get("ZEJZLAI_DECISION_GATE"))
        allow_remote = _flag(env.get("ZEJZLAI_DECISION_GATE_ALLOW_REMOTE"))
        try:
            timeout = float(env.get("ZEJZLAI_DECISION_GATE_TIMEOUT", DEFAULT_TIMEOUT))
            threshold = float(env.get("ZEJZLAI_DECISION_GATE_THRESHOLD", DEFAULT_THRESHOLD))
        except ValueError:
            logger.warning("Decision gate: bad timeout/threshold value, using defaults")
            timeout, threshold = DEFAULT_TIMEOUT, DEFAULT_THRESHOLD
        try:
            return cls(
                enabled=enabled,
                base_url=env.get("ZEJZLAI_DECISION_GATE_URL", DEFAULT_BASE_URL),
                model=env.get("ZEJZLAI_DECISION_GATE_MODEL", DEFAULT_MODEL),
                timeout=timeout,
                threshold=threshold,
                tiers=parse_tiers(env.get("ZEJZLAI_DECISION_GATE_TIERS")),
                allow_remote=allow_remote,
            )
        except NonLocalURLError as exc:
            # Never crash the app over an optional feature: disable the gate.
            logger.warning("Decision gate disabled: %s", exc)
            return cls(enabled=False)

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.base_url + ENDPOINT, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def classify(self, content: str) -> Optional[GateDecision]:
        """Return the tier decision, or None (disabled, error, slow, unsure)."""
        if not self.enabled or not content:
            return None
        payload = {
            "model": self.model,
            "state": content[:MAX_STATE_CHARS],
            "questions": {"size": SIZE_QUESTION},
        }
        start = time.perf_counter()
        try:
            data = await asyncio.wait_for(self._post(payload), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.info("Decision gate timeout after %.0f ms (%s), using default provider",
                        (time.perf_counter() - start) * 1000, content_fingerprint(content))
            return None
        except Exception as exc:  # fail open on anything
            logger.info("Decision gate unavailable (%s), using default provider",
                        type(exc).__name__)
            return None
        latency_ms = (time.perf_counter() - start) * 1000

        try:
            answer = data["answers"]["size"]
            tier = str(answer["choice"]).lower()
            probabilities = {str(k).lower(): float(v)
                             for k, v in (answer.get("probabilities") or {}).items()}
            probability = probabilities.get(tier, float(answer.get("confidence", 0.0)))
        except (KeyError, TypeError, ValueError, AttributeError):
            logger.info("Decision gate: unexpected response shape, using default provider")
            return None

        if tier not in TIERS:
            logger.info("Decision gate: unknown tier %r, using default provider", tier)
            return None
        if probability < self.threshold:
            logger.info("Decision gate: tier=%s p=%.2f below threshold %.2f (%.0f ms, %s), "
                        "using default provider", tier, probability, self.threshold,
                        latency_ms, content_fingerprint(content))
            return None
        return GateDecision(tier=tier, probability=probability, latency_ms=latency_ms,
                            provider=self.tiers.get(tier), probabilities=probabilities)

    async def route(self, content: str, available: Iterable[str]) -> Optional[str]:
        """Return a registered provider name for the message, or None."""
        decision = await self.classify(content)
        if decision is None:
            return None
        available = {p.lower() for p in available}
        provider = (decision.provider or "").lower()
        if provider not in available:
            logger.info("Decision gate: tier=%s maps to %r which is not registered, "
                        "using default provider", decision.tier, provider)
            return None
        logger.info("Decision gate: tier=%s p=%.2f latency=%.0f ms provider=%s (%s)",
                    decision.tier, decision.probability, decision.latency_ms, provider,
                    content_fingerprint(content))
        return provider
