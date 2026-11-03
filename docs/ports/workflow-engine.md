# Port: GG workflow engine from grokputer

Part of [the grokputer ports plan](../plans/2026-11-03-grokputer-ports.md). Status: built 2026-11-04 as zejzlAI PRs #13 (core), #14 (wiring) and #15 (bus); each waits for Zejzl's merge. Differences from
this design: the core PR got its own runner (`python -m src.workflow.run`, exit 0/1/2) because the seven ported CLI tests needed
one; menu item 9 is Workflow Mode and Quit moved to 10; `grokputer`'s `messagebus_adapter.py` was not copied but rewritten against
the real bus API (see bus-send-and-wait.md); `pantheon_integration.py` stays out (its agents do not exist here; `AgentNode` covers
Pantheon steps); the API route is not built. Design text below as written on 2026-11-03.

## What grokputer has (verified)

`~/Projects/grokputer/src/workflow/`, 19 files, 4,964 lines, 88 tests in `tests/workflow/` (all pass locally on Python 3.14).

| File | Lines | What |
|---|---|---|
| `engine.py` | 453 | `WorkflowEngine`: DAG with topological order (`get_execution_order`), parallel batches of independent nodes (`get_parallel_batches`), per-node execution with status, `run` and `execute` |
| `flow.py` | 159 | `Workflow` DSL: `add_node`, `add_edge(from, to, condition=...)`, `validate`, `run`, callbacks `on_start`, `on_complete`, `on_node_start`, `on_node_complete`, `on_error` |
| `loader.py` | 171 | Build a `Workflow` from YAML or JSON: `name`, `timeout`, `input`, `nodes` (id, type, config), `edges` (pairs or `{from, to, condition}`). `${VAR}` in config strings reads the environment, so tokens stay out of files. Node types: http, conditional, transform, ai, notion, asana, slack, noop |
| `state.py` | 512 | `StateManager`: in-memory key/value state plus SQLite snapshots (`create_snapshot`, `restore_snapshot`, `list_snapshots`), `get_workflow_context`, `update_from_context`, stats |
| `healing.py` | 448 | `WorkflowHealer`: retry strategies, fallback nodes, failure detection; an optional "fairy magic" hook (`src.magic.FairyMagic`) inside a try/except ImportError |
| `learning.py` | 401 | Tracks execution performance and tunes node configs (Q-learning style). Unverified value |
| `nodes/base.py` | 231 | `NodeStatus`, `NodeContext` (`get`/`set` data, `get_state`/`set_state`), `BaseNode` (`execute` abstract, `run` wraps it with status and timing, `connect_to`, `to_dict`), `StartNode`, `EndNode`, `NoOpNode` |
| `nodes/http.py` | 248 | GET, POST, PUT, DELETE, PATCH via `aiohttp`, headers, params, body, auth, retries. Tests mock `aiohttp.ClientSession` |
| `nodes/conditional.py` | 199 | if/else branching, comparison and logic operators, custom evaluator. Edge conditions "true"/"false" skip the other branch; skips propagate |
| `nodes/transform.py` | 138 | Custom function or `operation: jq` with a path expression (a small built-in path extractor, not the jq library) |
| `nodes/ai_node.py` | 192 | Prompt a provider; `_invoke_provider` imports `src.grok_client.GrokClient` lazily |
| `nodes/slack.py`, `notion.py`, `asana.py` | 790 | API integrations, each needs a token |
| `messagebus_adapter.py` | 466 | Publishes workflow events on the in-process bus; `MessageBusNode`. Lazy `from src.core.message_bus import ...` |
| `pantheon_integration.py` | 429 | Delegates a node to a grokputer Pantheon agent over the bus |

Coupling outside the package: only the three lazy imports above (`src.grok_client`, `src.core.message_bus`, `src.magic`). Nothing else.
PyYAML is required by the loader; `aiohttp` by the http node. Five log lines contain emojis (not allowed in zejzlAI `.py` files).

Tests by file: ai_node 12, branching 13, engine 9, healing 22, loader 14, nodes 18.

## What zejzlAI has

- `src/workflows.py`, 333 lines: `WorkflowStep` subclasses (agent step, parallel group, conditional branch, loop), `WorkflowDefinition`,
  `WorkflowExecutor` over a step list. No DAG, no loader, no persistence, no retries. Imported by nothing in `src/`, `tests/` or the
  root scripts, so it has no tests and no runtime.
- The live path is `main.py` menu -> `ai_framework.py` -> `src/agents/*` (`observe`, `reason`, `act`, ...) calling providers through
  the provider bus `base.get_ai_provider_bus().send_message(content, provider_name, conversation_id)`, and ORAM via
  `src/oram.py` `execute_oram(task, iteration_type, max_iterations)` (menu item 8).
- The in-process bus `src/core/message_bus.py` is imported by `base.py` (the `PantheonAgent` ABC) and `benchmark_comparison.py` only.
  No live code path sends on it.

## Design for zejzlAI

New package `src/workflow/` (singular, as in grokputer). The engine runs in-process inside whatever calls it (menu, later the API).

**Keep as is (PR 1):** `engine.py`, `flow.py`, `loader.py`, `state.py`, `healing.py`, `nodes/base.py`, `nodes/http.py`,
`nodes/conditional.py`, `nodes/transform.py`, and the tests for them. Changes while copying:
- remove the five emoji log lines; replace with `[OK]`/`[INFO]` tags;
- remove the `FairyMagic` hook in `healing.py` (zejzlAI has its own `src/magic.py`; the hook is decoration, not healing);
- `state.py` SQLite path from a constructor argument with a default under the existing data directory, never cwd;
- one header line per file: `# Ported from grokputer src/workflow/<file> at <sha>, 2026-11`;
- `requirements.txt`: add `PyYAML` (grokputer pins 6.0.3).

**Leave out:** `learning.py` (unverified RL tuning), `slack.py`, `notion.py`, `asana.py` (tokens; add back one at a time if a workflow
needs them), `messagebus_adapter.py` and `pantheon_integration.py` (they target the in-process bus, which has no live consumer here;
see [bus-send-and-wait.md](bus-send-and-wait.md)).

**New nodes (PR 2):**
- `AgentNode(agent="observer", method="observe", provider=None)`: calls the named Pantheon agent in `src/agents/` with the context's
  input, stores the dict result under the node id. Replaces grokputer's `ai_node.py`, whose `GrokClient` does not exist here. A plain
  `prompt` form calls `send_message` on the provider bus directly, same degrade-to-rule-based behaviour the agents use.
- `ORAMNode(iteration_type="basic", max_iterations=3)`: one `execute_oram` run; the cap follows Zejzl's ORAM decision (3 iterations).
- Both are registered in the loader's type table (`agent`, `oram`).

**Entry points (PR 2):** menu item "Run a workflow file" in `main.py` next to ORAM mode; `examples/workflows/observe-reason-act.yaml`
(observer -> reasoner -> actor with a conditional on the reasoner's confidence) and `examples/workflows/http-summarise.yaml`
(http -> transform -> agent). README section "Workflows" with the YAML format and the node table.

**Cleanup (PR 3, optional):** delete `src/workflows.py`; `POST /workflows/run` in `web_dashboard.py` behind the existing API key auth
(admin tier), request body = the YAML/JSON definition, response = node statuses and the final context. Bringing in
`messagebus_adapter.py` belongs here too, if and only if something listens on the bus by then.

## Tests

- Port the 76 tests of the kept files unchanged where possible (ai_node tests are replaced by `AgentNode` tests).
- `AgentNode` and `ORAMNode` tests fake the provider bus like `tests/test_agent_fallbacks.py` (monkeypatch `base.get_ai_provider_bus`)
  and `execute_oram` with a stub; `tests/conftest.py` already refuses network, so a forgotten mock fails loudly.
- Loader tests gain the two new node types and an example-file smoke test (load every file in `examples/workflows/`, validate, do not run).
- Gates: `python -m pytest -q`, `flake8 . --count --select=E9,F63,F7,F82`.

## Risks and open points

- zejzlAI is a production-deploy repo: PR 1 touches no live path, but still merges only on Zejzl's yes.
- Name clash in reading, not in code: `src/workflows.py` (old) next to `src/workflow/` (new) until PR 3. Say so in the README until then.
- `state.py` opens SQLite; CI on the hosted platform needs a writable path (default to a temp directory when the data directory is read-only).
- grokputer's engine has had no production use either; "88 tests pass" is the whole evidence. The example workflows in PR 2 are the first real run.
- Keep the copy honest: when grokputer's `src/workflow/` changes, note it in both hubs in brain; the header sha makes the diff cheap.
