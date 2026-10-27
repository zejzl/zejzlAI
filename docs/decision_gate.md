# Decision gate (local model router, pilot)

`src/decision_gate.py` lets zejzlAI pick a provider per message with a small
local decision model instead of always using `default_provider`.

## What it does

When `send_message` is called **without** a provider name (and not in
consensus mode), the gate asks a local System One model (Clef via Ollama's
Jev-compatible `/v1/systemone` endpoint) one question: does this message need
a `small`, `medium` or `large` model? The answer is mapped to a provider:

| Tier   | Default provider | Default model (config)          |
|--------|------------------|---------------------------------|
| small  | gemini           | gemini-2.5-flash-lite           |
| medium | grok             | grok-4-1-fast-reasoning         |
| large  | claude           | claude-sonnet-4-5               |

The gate fails open: if it is off, Ollama is down or slower than the timeout,
the answer is malformed, the probability is below the threshold, or the
mapped provider is not registered, `send_message` uses `default_provider`
exactly as before. An explicit `provider_name` always wins.

Warm latency on an RX 7900 XT with `clef-flash` is about 75-100 ms per call.

## Enable it

```bash
# 1. Local Ollama with a Clef model, listening on 127.0.0.1:11434
ollama pull clef-flash

# 2. Turn the gate on (off by default)
export ZEJZLAI_DECISION_GATE=1
```

Optional settings:

| Variable                             | Default                  |
|--------------------------------------|--------------------------|
| `ZEJZLAI_DECISION_GATE_URL`          | `http://127.0.0.1:11434` |
| `ZEJZLAI_DECISION_GATE_MODEL`        | `clef-flash`             |
| `ZEJZLAI_DECISION_GATE_TIMEOUT`      | `1.0` (seconds)          |
| `ZEJZLAI_DECISION_GATE_THRESHOLD`    | `0.7`                    |
| `ZEJZLAI_DECISION_GATE_TIERS`        | `small=gemini,medium=grok,large=claude` |
| `ZEJZLAI_DECISION_GATE_ALLOW_REMOTE` | off                      |

Each routed message logs the tier, probability, latency and chosen provider
under the `DecisionGate` logger.

## Privacy

- The gate only talks to localhost by default. A non-local URL disables the
  gate (with a warning) unless `ZEJZLAI_DECISION_GATE_ALLOW_REMOTE=1` is set.
- Only the first 4000 characters of the message are sent to the local model.
- Logs contain the message length and a short SHA-256 prefix, never the text.

## Tests

`tests/test_decision_gate.py` mocks the HTTP call, so CI needs no Ollama. To
also run one real call against a local Ollama:

```bash
ZEJZLAI_TEST_LOCAL_GATE=1 python -m pytest tests/test_decision_gate.py -k real_local
```
