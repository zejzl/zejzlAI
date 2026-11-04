# src/agents/memory.py
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("MemoryAgent")

# File backend for ORAM runs. Off unless ORAM_MEMORY_DIR names a directory; then every completed ORAM loop appends
# one JSON object to <dir>/<task key>.jsonl and the Reason step reads earlier lines of the same file back.
MEMORY_DIR_ENV = "ORAM_MEMORY_DIR"
TEXT_CAP = 2000          # longest stored summary/result text, in characters
SLUG_LEN = 40            # task key = slug of the task text (this long) + short hash of the full text

# Ranked recall (on trial): with ORAM_MEMORY_RANKED=1 the Reason step sees the best-matching earlier runs of ANY task,
# not only the same task key. Score = word overlap with the current task (dominant) plus recency (tie-breaker). The
# stored quality score is deliberately not used: every run scores 0.95 today (structural scorer), so it ranks nothing.
RANKED_ENV = "ORAM_MEMORY_RANKED"
RECENCY_HALF_LIFE_DAYS = 7.0
OVERLAP_WEIGHT, RECENCY_WEIGHT = 0.8, 0.2
TASK_OVERLAP_WEIGHT, CONTENT_OVERLAP_WEIGHT = 0.7, 0.3
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.-]+")
_STOPWORDS = frozenset("""
a an the and or of in on at to for from by with as is are was were be been it its this that these those what which
who how why when where into onto over under about via per each all any some not no do does did done can could
should would will shall may might must our your their my his her we you they them us me i if then than so such
up out off only also just very more most less least new old one two three
""".split())


def ranked_enabled() -> bool:
    """True when ORAM_MEMORY_RANKED is 1/true/yes/on."""
    return os.environ.get(RANKED_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def tokens(text: Any) -> frozenset:
    """Lower-case words of at least two characters, minus stopwords. Punctuation inside words (file.py) is kept."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    return frozenset(t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS)


def _age_days(ts: Any, now: datetime) -> Optional[float]:
    try:
        then = datetime.fromisoformat(str(ts))
    except (TypeError, ValueError):
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return max((now - then).total_seconds(), 0.0) / 86400.0


def score_run(run: Dict[str, Any], query: frozenset, now: Optional[datetime] = None) -> float:
    """Relevance of a stored run to the tokens of the current task. 0.0 when they share no word at all.

    overlap  = 0.7 * (query words found in the stored task) + 0.3 * (query words found in its insights/summary/result),
               both as a fraction of the query, so the same task scores 1.0 on the first term;
    recency  = 0.5 ** (age in days / 7);
    score    = 0.8 * overlap + 0.2 * recency   (recency only orders runs with the same overlap).
    """
    if not query:
        return 0.0
    now = now or datetime.now(timezone.utc)
    task_words = tokens(run.get("task"))
    content = [run.get("summary"), run.get("result")] + list(run.get("insights") or [])
    content_words = frozenset().union(*(tokens(c) for c in content)) if content else frozenset()
    task_overlap = len(query & task_words) / len(query)
    content_overlap = len(query & content_words) / len(query)
    overlap = TASK_OVERLAP_WEIGHT * task_overlap + CONTENT_OVERLAP_WEIGHT * content_overlap
    if overlap == 0.0:
        return 0.0
    age = _age_days(run.get("ts"), now)
    recency = 0.5 ** (age / RECENCY_HALF_LIFE_DAYS) if age is not None else 0.0
    return OVERLAP_WEIGHT * overlap + RECENCY_WEIGHT * recency


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
        # Parsed JSONL files for ranked recall, keyed by path, invalidated when a file's mtime or size changes.
        self._runs_cache: Dict[Path, Tuple[Tuple[int, int], List[Dict[str, Any]]]] = {}

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

    def _read_runs(self, path: Path) -> List[Dict[str, Any]]:
        """All runs in one JSONL file, oldest first. A corrupt line is skipped; an unreadable file is an empty list."""
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
        return runs

    def recall_runs(self, task: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Earlier runs of `task` (exact task key), newest first. A missing file is an empty list."""
        path = self._run_file(task)
        if path is None or limit <= 0 or not path.is_file():
            return []
        runs = self._read_runs(path)
        runs.reverse()
        return runs[:limit]

    def _all_runs(self) -> List[Dict[str, Any]]:
        """Every run in every JSONL file of the memory directory, through the per-file cache."""
        if self.memory_dir is None or not self.memory_dir.is_dir():
            return []
        runs: List[Dict[str, Any]] = []
        seen = set()
        for path in sorted(self.memory_dir.glob("*.jsonl")):
            try:
                stat = path.stat()
            except OSError:
                continue
            stamp = (stat.st_mtime_ns, stat.st_size)
            cached = self._runs_cache.get(path)
            if cached is None or cached[0] != stamp:
                cached = (stamp, self._read_runs(path))
                self._runs_cache[path] = cached
            seen.add(path)
            runs.extend(cached[1])
        for stale in [p for p in self._runs_cache if p not in seen]:
            del self._runs_cache[stale]
        return runs

    def recall_ranked(self, task: str, limit: int = 5) -> List[Dict[str, Any]]:
        """The `limit` earlier runs of ANY task that best match `task` (see score_run), best first.

        A run that shares no word with the task is never returned, so an unrelated history yields an empty list
        just like the exact-match recall does. Empty when the backend is off.
        """
        if self.memory_dir is None or limit <= 0:
            return []
        query = tokens(task)
        if not query:
            return []
        now = datetime.now(timezone.utc)
        scored = []
        for index, run in enumerate(self._all_runs()):
            score = score_run(run, query, now)
            if score > 0.0:
                scored.append((score, str(run.get("ts", "")), index, run))
        scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        return [item[3] for item in scored[:limit]]

    def recall_prior(self, task: str, limit: int = 5) -> List[Dict[str, Any]]:
        """What the Reason step gets: ranked cross-task recall when ORAM_MEMORY_RANKED is on, else the exact task."""
        if ranked_enabled():
            return self.recall_ranked(task, limit=limit)
        return self.recall_runs(task, limit=limit)


def format_prior_runs(runs: List[Dict[str, Any]], max_chars: int = 240, task: Optional[str] = None) -> List[str]:
    """One short line per earlier run, for the reasoning prompt.

    With `task` given, a run of a different task (ranked recall) is prefixed with `[task: ...]` so the model knows
    it is looking at a related run, not an earlier attempt at the same one.
    """
    lines = []
    current = task_key(task) if task else None
    for run in runs:
        ts = str(run.get("ts", ""))[:16].replace("T", " ")
        quality = run.get("best_quality", run.get("average_quality"))
        quality_text = f"{quality:.2f}" if isinstance(quality, (int, float)) else "?"
        text = run.get("summary") or run.get("result") or ""
        prefix = ""
        run_task = run.get("task")
        if current and isinstance(run_task, str) and task_key(run_task) != current:
            prefix = f"[task: {' '.join(run_task.split())[:60]}] "
        line = f"{prefix}{ts} quality {quality_text}, {run.get('iterations', '?')} iterations: {text}"
        lines.append(line[:max_chars])
    return lines
