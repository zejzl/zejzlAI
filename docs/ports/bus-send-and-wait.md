# Port: `send_and_wait` for the in-process message bus

Part of [the grokputer ports plan](../plans/2026-11-03-grokputer-ports.md). Status: built 2026-11-04 in zejzlAI PR #15, with its consumers in the same PR (Zejzl: "async messagebus implementation"):
`send_and_wait` ported with 7 tests; `src/core/bus_agent.py` adds `BusAgent` (the receive-process-reply loop that puts the
request's `correlation_id` on replies, after grokputer's `BaseAgent.run`) and `ProviderBusAgent` (answers prompt requests through
the provider bus); `src/workflow/messagebus_adapter.py` gives workflows `publish`, `request`, `broadcast` and node type `bus`.
grokputer's adapter was not copied: it used a Message shape and a `bus.publish` the bus never had, and simulated subscriptions.
`base.PantheonAgent` is left as it was (its bus calls target an API this bus does not have). Design text below as written.

## The two buses today (verified)

`zejzlAI/src/core/message_bus.py` (783 lines) and `grokputer/src/core/message_bus.py` (825 lines) are the same file, ported to zejzlAI
in January 2026. `diff` shows 86 changed lines, in two groups:

- grokputer added `async def send_and_wait(self, to_agent, message, timeout=None) -> dict` (October 2026): send a message to an agent
  and return that agent's reply, defined as the first message sent *from* `to_agent` carrying the request's `correlation_id`. The
  interception happens inside `send()`, so the caller's own receive loop is not involved and it does not matter whom the reply is
  addressed to. `BaseAgent.run` copies the `correlation_id` onto replies. Tests: 7 in `tests/core/test_send_and_wait.py`, 1 in
  `tests/agents/test_plain_agents.py`, all pass.
- zejzlAI has a TOON block that is a placeholder: `TOON_AVAILABLE = False`, the real import is commented out, and `ToonDecodeError`
  is a stub so that `send_toon`/`receive_toon` raise. There is nothing to carry back to grokputer.

Zejzl's decision (2026-11-03, via Hermes): both buses stay, the fork is noted; neither becomes canonical.

## Who uses zejzlAI's bus

`base.py` imports `MessageBus` and `Message` for the `PantheonAgent` ABC; `benchmark_comparison.py` imports it for a benchmark.
The live path (menu -> `ai_framework` -> `src/agents/*` -> provider bus -> ORAM) never sends on it. So today a backported
`send_and_wait` would be a method with no caller.

## When it becomes worth doing

Either of these creates a caller:
1. The workflow engine's `messagebus_adapter.py` and `pantheon_integration.py` come in (workflow PR 3 in the plan): a workflow node
   that delegates to a Pantheon agent over the bus needs exactly "send and wait for the reply".
2. Hermes's option A (brain `inbox/2026-11-03-oram-messagebus-room-integration.md`): an ORAM service that the room runner talks to;
   its request/reply shape is the same.

## How to do it (size S, one PR)

- Copy `send_and_wait` and the few lines in `send()` that resolve a pending future by `correlation_id` from grokputer's file at the
  noted sha; keep zejzlAI's TOON block as it is.
- Port the 7 tests from `tests/core/test_send_and_wait.py` (they use the bus alone, no network). The `test_plain_agents` case depends
  on grokputer's `BaseAgent`, so replace it with a test on `base.PantheonAgent` once a subclass exists that replies with the `correlation_id`.
- Note the change in both brain hubs (`projects/zejzlAI/index`, `projects/grokputer/index`) so the fork distance stays known.
- Gates as usual: `python -m pytest -q`, `flake8 . --count --select=E9,F63,F7,F82`; Zejzl's yes to merge.

## Not doing

Merging the two files into one shared package, or making one canonical: Zejzl decided both stay. Adding TOON for real: nothing asks for it.
