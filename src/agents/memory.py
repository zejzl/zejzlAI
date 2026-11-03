# src/agents/memory.py
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger("MemoryAgent")

# File backend for ORAM runs. Off unless ORAM_MEMORY_DIR names a directory; then every completed ORAM loop appends
# one JSON object to <dir>/<task key>.jsonl and the Reason step reads earlier lines of the same file back.
MEMORY_DIR_ENV = "ORAM_MEMORY_DIR"
TEXT_CAP = 2000          # longest stored summary/result text, in characters
SLUG_LEN = 40            # task key = slug of the task text (this long) + short hash of the full text

# Anything that looks like a provider key or bearer token. The task text and the agents' answers can carry one by
# accident (a pasted .env line, a URL with a key); the file lives outside the repo but is still plain text.
_SECRET_PATTERNS = [
    re.compile(r"\b(?:sk|xai|gsk|ghp|gho|ghu|ghs|ghr|xoxb|xoxp)[-_][A-Za-z0-9_-]{16,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{16,}"),
    re.compile(r"(?i)\b([A-Z0-9_]*(?:api[_-]?key|secret|token|password)[A-Z0-9_]*)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
]
_REDACTED = "[REDACTED]"


def scrub_secrets(text: str) -> str:
    """Replace key- and token-shaped substrings with [REDACTED]. Keeps the key NAME of a `NAME=value` pair."""
    if not isinstance(text, str):
        text = str(text)

    def _sub(match):
        if match.lastindex:
            return f"{match.group(1)} {_REDACTED}"
        return _REDACTED

    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_sub, text)
    return text


def task_key(task: str) -> str:
    """File name (without extension) for a task: a readable slug plus a hash of the full text."""
    normalised = " ".join(str(task).split()).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalised).strip("-")[:SLUG_LEN].strip("-") or "task"
    digest = hashlib.sha1(normalised.encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{digest}"


def memory_dir() -> Optional[Path]:
    """The configured directory, or None when the file backend is off."""
    value = os.environ.get(MEMORY_DIR_ENV, "").strip()
    return Path(value).expanduser() if value else None


class MemoryAgent:
    """
    Memory Agent for Pantheon 9-Agent System.
    Responsible for storing and recalling state, observations, and execution history.

    Specialization: State Management & Historical Data
    Responsibilities:
    - Store and organize system events and data
    - Provide efficient data retrieval and filtering
    - Maintain conversation and execution history
    - Support memory-based decision making

    Expertise Areas:
    - Data persistence and storage optimization
    - Memory retrieval and search algorithms
    - Historical data analysis
    - State management and caching

    Events (`store`/`recall(filter_fn)`) live in an in-process list, as before. Completed ORAM runs can additionally
    go to disk (`store_run`/`recall(task, limit)`) when ORAM_MEMORY_DIR is set; without it both are no-ops.
    """

    def __init__(self):
        self.name = "Memory"
        self.specialization = "State Management & Historical Data"
        self.responsibilities = [
            "Store and organize system events and data",
            "Provide efficient data retrieval and filtering",
            "Maintain conversation and execution history",
            "Support memory-based decision making"
        ]
        self.expertise_areas = [
            "Data persistence and storage optimization",
            "Memory retrieval and search algorithms",
            "Historical data analysis",
            "State management and caching"
        ]
        self.memory_store: List[Dict[str, Any]] = []
        self.memory_dir: Optional[Path] = memory_dir()

    @property
    def file_backend_enabled(self) -> bool:
        return self.memory_dir is not None

    async def store(self, event: Dict[str, Any]):
        """
        Store an event in memory (stub).
        """
        self.memory_store.append(event)
        logger.info(f"[{self.name}] Stored event: {event}")

    async def recall(self, filter_fn: Union[Callable, str, None] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recall events from memory. Optionally apply a filter function.

        Given a task string instead of a filter, return that task's earlier ORAM runs from the file backend,
        newest first, at most `limit` (empty when the backend is off).
        """
        if isinstance(filter_fn, str):
            return self.recall_runs(filter_fn, limit=limit)
        recalled = [e for e in self.memory_store if filter_fn(e)] if filter_fn else self.memory_store
        logger.info(f"[{self.name}] Recalled {len(recalled)} events")
        return recalled

    # --- file backend ---------------------------------------------------------------------------

    def _run_file(self, task: str) -> Optional[Path]:
        return self.memory_dir / f"{task_key(task)}.jsonl" if self.memory_dir else None

    def store_run(self, task: str, record: Dict[str, Any]) -> Optional[Path]:
        """Append one completed ORAM run for `task` to its JSONL file. Returns the path, or None when off."""
        path = self._run_file(task)
        if path is None:
            return None
        entry: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "task": scrub_secrets(task)[:TEXT_CAP],
        }
        for key, value in record.items():
            if isinstance(value, str):
                value = scrub_secrets(value)[:TEXT_CAP]
            elif isinstance(value, list):
                value = [scrub_secrets(v)[:TEXT_CAP] if isinstance(v, str) else v for v in value]
            entry[key] = value
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        logger.info(f"[{self.name}] Stored run for task key {path.stem}")
        return path

    def recall_runs(self, task: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Earlier runs of `task`, newest first. A corrupt line is skipped; a missing file is an empty list."""
        path = self._run_file(task)
        if path is None or limit <= 0 or not path.is_file():
            return []
        runs: List[Dict[str, Any]] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            logger.warning(f"[{self.name}] Could not read {path.name}: {exc}")
            return []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"[{self.name}] Skipping a corrupt line in {path.name}")
                continue
            if isinstance(parsed, dict):
                runs.append(parsed)
        runs.reverse()
        return runs[:limit]


def format_prior_runs(runs: List[Dict[str, Any]], max_chars: int = 240) -> List[str]:
    """One short line per earlier run, for the reasoning prompt."""
    lines = []
    for run in runs:
        ts = str(run.get("ts", ""))[:16].replace("T", " ")
        quality = run.get("best_quality", run.get("average_quality"))
        quality_text = f"{quality:.2f}" if isinstance(quality, (int, float)) else "?"
        text = run.get("summary") or run.get("result") or ""
        line = f"{ts} quality {quality_text}, {run.get('iterations', '?')} iterations: {text}"
        lines.append(line[:max_chars])
    return lines
