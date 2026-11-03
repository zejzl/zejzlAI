# Plan: what to take from grokputer into zejzlAI (2026-11-03)

Author: Claude, on Zejzl's ask ("is there anything in grokputer that can be used in zejzlAI?" then "make a plan & docs for all 3").
Status: plan, nothing built. Facts below were read from both checkouts on 2026-11-03 evening; "unverified" marks what was not run.

## Result of the comparison

Most of grokputer already has a counterpart here: the in-process message bus (ported in January, 86 lines apart today), ORAM
(`src/oram.py`, fuller than grokputer's), the MAF ideas (consensus voting, swarm wrapper, Pantheon RLM), healing, learning loop,
multimodal and security modules. Those stay as they are; Zejzl decided on 2026-11-03 that both buses stay (fork noted) and MAF stays.

Three pieces have substance that zejzlAI lacks. Each has its own doc in `docs/ports/`:

| # | Piece | grokputer | zejzlAI today | Verdict | Doc |
|---|---|---|---|---|---|
| 1 | GG workflow engine | `src/workflow/`, 19 files, 4,964 lines, 88 tests pass | `src/workflows.py`, 333 lines, step list, no DAG, loader or persistence, imported by nothing | **take**, in three PRs | [workflow-engine.md](../ports/workflow-engine.md) |
| 2 | Hierarchical memory tiers | `src/memory/hierarchical_memory.py`, 728 lines, 13 tests pass | `MemoryAgent` list plus Hermes's file backend (PR #11, today) | **wait** for Hermes's ORAM step 2, then decide | [memory-tiers.md](../ports/memory-tiers.md) |
| 3 | Bus `send_and_wait` | 1 method, 8 tests | bus has request/response but no wait-for-reply helper; bus has no live consumer | **only with a consumer**, as part of #1 or Hermes's option A | [bus-send-and-wait.md](../ports/bus-send-and-wait.md) |

Not relevant here and not planned: Wayland and PyAutoGUI control (zejzlAI is a hosted service), QLoRA training, the haiku and dice
tools, the "flash attention" cognitive module, blockchain, vault sync.

## Order of work

1. **Workflow engine, PR 1 (core, no wiring).** Copy engine, flow, loader, state, healing, the node base and the http, conditional,
   transform and noop nodes with their tests into `src/workflow/`. Add PyYAML. Strip the five emoji log lines. No menu or API change,
   so nothing that runs today changes. Size M (about 2,700 lines moved, 76 tests).
2. **Workflow engine, PR 2 (wiring).** `AgentNode` (a Pantheon agent step through the provider bus) and `ORAMNode` (one `execute_oram`
   run), a menu item "Run a workflow file", an example in `examples/workflows/`, a README section. Size S-M.
3. **Workflow engine, PR 3 (cleanup, optional).** Delete `src/workflows.py` (no importers, no tests), and if wanted a `POST /workflows/run`
   in `web_dashboard.py` behind the existing API key auth. Size S.
4. **Memory tiers.** Decide after Hermes's ORAM step 2 (three real runs filed in brain) shows whether runs are worth remembering.
   If yes: port `MemoryEntry`, `ShortTermMemory`, `ContextMemory` (227 lines) under Hermes's file backend, opt-in. Hermes's lane; agree
   with him first.
5. **Bus `send_and_wait`.** Backport only when something in zejzlAI waits for an agent's reply on the in-process bus: the workflow bus
   adapter if PR 3 brings it in, or Hermes's option A. Alone it adds a method nobody calls.

## Rules that apply

- zejzlAI deploys on merge to `main` (`~/CLAUDE.md`, Git section): every PR here waits for Zejzl's yes to merge. Branches and PRs are free.
- Tests stay offline (`tests/conftest.py` refuses sockets and sets dummy keys). HTTP node tests already mock `aiohttp`; agent and ORAM
  node tests fake the provider bus the way `tests/test_agent_fallbacks.py` does.
- Before each PR: `python -m pytest -q` and `flake8 . --count --select=E9,F63,F7,F82` (grokputer's workflow and memory code is clean
  on that gate today). No emojis in `.py`; console tags `[OK]`, `[WARNING]`, `[ERROR]`, `[INFO]`.
- Ported files keep grokputer's history reference in a one-line header comment (`Ported from grokputer src/workflow/engine.py at <sha>`),
  so later diffs between the two repos stay possible. Zejzl's decision: both repos keep their own copy of shared code, with the fork noted.

## Decisions for Zejzl

1. Go for PR 1 and PR 2 of the workflow engine? Default: yes, PR 1 first, merged only on your yes.
2. Node set in PR 1: http, conditional, transform, noop only, or also Slack, Notion, Asana (each needs a token through `${VAR}`)? Default: without them.
3. Delete `src/workflows.py` in PR 3? Default: yes (nothing imports it, no tests).
4. Memory tiers: wait for Hermes's step 2? Default: yes.
5. `send_and_wait`: only with a consumer? Default: yes.

## How to check this plan's claims

```bash
cd ~/Projects/grokputer && .venv/bin/python -m pytest -q tests/workflow tests/memory tests/core/test_send_and_wait.py
cd ~/Projects/zejzlAI && grep -rn 'workflows' --include=*.py src tests *.py | grep import   # empty
cd ~/Projects/zejzlAI && .venv/bin/python -m pytest -q                                         # 212 passed, 2 skipped on 2026-11-03
```
