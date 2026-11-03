# Port: hierarchical memory tiers from grokputer

Part of [the grokputer ports plan](../plans/2026-11-03-grokputer-ports.md). Status: design, **waiting** on Hermes's ORAM step 2.
Read on 2026-11-03. Owner of the zejzlAI memory lane today: Hermes (PR #11 merged 2026-11-03, `f511630`).

## What grokputer has (verified)

`~/Projects/grokputer/src/memory/`, 8 files. Tests: 13 in `tests/memory/test_hierarchical_memory.py`, all pass locally.

| Piece | Lines | What |
|---|---|---|
| `MemoryEntry` | ~25 | content, metadata, timestamps, access count, a relevance score that decays with age and rises with access |
| `ShortTermMemory` | ~80 | LRU working memory with a size cap, access ordering, keyword search |
| `ContextMemory` | ~125 | session memory with decay and consolidation into fewer, summarised entries |
| `HierarchicalMemoryManager(MemoryBackend)` | ~470 | three tiers (short-term, context, long-term through a backend), `store_episode`, `retrieve_context`, `consolidate`, stats, background consolidation task |
| backends | 373 | `redis_store.py` (needs a Redis), `pinecone_store.py` (needs Pinecone, `sentence_transformers`, and HyDE through grokputer's `FallbackGrokClient`) |
| managers | 196 | `memory_factory.py` picks a backend from config with fallback; `persistent_manager.py` is a SQLite store |

Coupling: `hierarchical_memory.py` imports grokputer's `src.encryption` (22 call sites, encrypt at rest), `src.knowledge_graph`
(2 call sites) and `src.exceptions`. The two tier classes plus `MemoryEntry` (lines 29-255, 227 lines) have none of that coupling.

Test names: short-term store/retrieve, LRU eviction, access ordering, search; context store/retrieve, decay, consolidation;
manager store episode, retrieve context, consolidate, stats, background consolidation; entry relevance.

## What zejzlAI has (after PR #11, today)

`src/agents/memory.py` `MemoryAgent`: an in-process list (`store`, `recall(filter_fn, limit)`) and, when `ORAM_MEMORY_DIR` names a
directory, a file backend: one JSONL file per task (`<slug>-<hash>.jsonl`), one JSON object per completed ORAM run (iterations, calls,
quality, insights, summary, result with text capped at 2000 characters and key-shaped strings redacted). The Reason step reads up to
5 earlier runs of the **same task** (`recall_runs(task)`) and passes them as `prior_runs`. Off by default. `src/memory.py` (the old
32-line copy) was deleted. Tests: `tests/test_oram_memory.py`.

Decisions already taken (Zejzl, 2026-11-03, via Hermes): cap 3 iterations per run; results go to the running agent's brain log and
`inbox/`; room posting by hand only. Hermes's step 2 (`scripts/oram_to_brain.py`, three real runs filed in brain) is parked until a
valid provider key is in `.env`. Neo's brain design ([[projects/brain/oram-memory-loop]] in brain) keeps consolidation as a weekly
PR and decay as "flag, don't forget"; its phases 2 and 3 need Zejzl's request.

## What the port would add, and what it would not

Would add, inside the process:
- a ranked `recall`: relevance = keyword overlap with the current task, recency, access count, with decay; today `recall_runs` is an
  exact match on the task key, so a run of "summarise the trading-lab README" does not surface for "write a README summary";
- cross-task recall over every JSONL file in `ORAM_MEMORY_DIR`, not just the current task's;
- a working-memory tier with an LRU cap and access ordering for the in-process list (today ORAM keeps the last 100 entries of its `memory_buffer`, oldest dropped, no ranking);
- consolidation of many similar runs into one summary entry (in memory only; the JSONL files stay append-only).

Would not add, by design: a second durable store (the JSONL files stay the only one, Redis and Pinecone backends are not ported),
encryption at rest (the redaction in `store_run` is the agreed protection), a knowledge graph, or anything that writes to brain
(that stays the agent's PR, per decision 0002 and Neo's design).

## Design, if Zejzl says go after step 2

- `src/agents/memory_tiers.py`: `MemoryEntry`, `ShortTermMemory`, `ContextMemory` ported from grokputer lines 29-255 with the
  grokputer imports replaced (plain exceptions, no encryption, no graph), header line with the grokputer sha.
- `MemoryAgent.recall(task, limit)` gains `ranked=True`: load runs from all JSONL files (cached per process), score them with
  `MemoryEntry.relevance`, return the top `limit`. `recall_runs(task)` keeps its exact-match behaviour for the Reason step until the
  ranked version is shown to help on real runs; then one line in `oram.py` switches it.
- `MemoryAgent.store` goes through `ShortTermMemory` (cap configurable, default 100) instead of the raw list; `recall(filter_fn)`
  keeps its signature.
- Off by default behind the existing `ORAM_MEMORY_DIR` (no new variable); ranked recall behind `ORAM_MEMORY_RANKED=1` while it is on trial.
- Tests: the 13 grokputer tests for the tier classes, adapted; ranked-recall tests over a temp directory of JSONL fixtures; everything offline.
- Size S (about 300 lines plus tests), one PR, Hermes's review since it is his lane, Zejzl's yes to merge.

## Why wait

Nothing shows yet that ORAM runs are worth recalling: the quality score is structural (Hermes's note, brain `inbox/2026-11-03-oram-messagebus-room-integration.md`),
the loop usually stops after one iteration, and no run has been filed in brain. Hermes's step 2 produces the first three real runs.
If their insights are empty, better recall ranks empty things; the port would be waste. If they are useful, this doc is ready.
