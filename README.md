# zejzlAI (zejzl.net)

A Python multi-agent framework that talks to several AI providers through one async message bus. You pick a mode from a menu
(single agent, two-provider collaboration, swarm, the 9-agent "Pantheon", a learning loop, offline mode, a community vault, and
ORAM mode), and there is a FastAPI web dashboard.

Status: personal project. The test suite and CI are green; most modes have not been exercised against live providers in a
recent session, so treat "works" as "runs and is tested offline" unless you try it with your own keys.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Python 3.11 to 3.13 in CI; 3.14 works locally
pip install -r requirements.txt
cp .env.example .env                                      # then add at least one provider key (see below)
python main.py                                            # interactive menu
```

Pick a mode by number. With no keys set, the agents still run but fall back to rule-based answers and say so in their output
(`ai_generated: False` plus a `fallback_reason` or `error`).

### Providers and keys

Keys go in `.env` (git-ignored). Never commit them. Default models are set in `ai_framework.py` (checked 2026-10-28):

| Provider | Variable | Default model |
|---|---|---|
| grok (default) | `GROK_API_KEY` | grok-4.3 |
| chatgpt | `OPENAI_API_KEY` | gpt-5-mini |
| claude | `ANTHROPIC_API_KEY` | claude-sonnet-5-5 |
| gemini | `GEMINI_API_KEY` | gemini-3.5-flash-lite |
| deepseek | `DEEPSEEK_API_KEY` | deepseek-coder |
| qwen | `QWEN_API_KEY` | qwen-turbo |
| zai | `ZAI_API_KEY` | zai-1 |

Other settings in `.env.example`: `REDIS_URL` (optional; without Redis the framework uses SQLite, set `SQLITE_PATH` to move
it) and the Stripe variables used by the payment module.

## Modes (`python main.py`)

1. Single Agent: Observe-Reason-Act loop.
2. Collaboration: two providers (Grok and Claude) plan together.
3. Swarm: several agents coordinated on the async bus.
4. Pantheon: the 9-agent system with validation and learning.
5. Learning Loop: one optimization cycle.
6. Offline: cached responses, no provider calls.
7. Community Vault: browse and share tools and configs.
8. ORAM: Observer, Reasoner, Actor plus Memory, iterated until the quality score converges (see below).
9. Quit.

### ORAM mode in short (`src/oram.py`)

Each iteration runs Observe, Reason, Act, then stores the result in Memory, scores it (0 to 1) and extracts up to three
insights. The loop stops when the score reaches the convergence threshold, when the quality trend declines, or at
`max_iterations`. Iteration types set defaults: basic 5 iterations at 0.85, deep analysis 7 at 0.9, creative 6 at 0.8,
problem solving 8 at 0.85, optimization 5 at 0.9. A `max_iterations` you set yourself wins over the type's default.
If a provider fails, the agents fall back to rule-based output; the iteration then carries an `error` key and scores lower.

## Web dashboard

```bash
uvicorn web_dashboard:app --host 127.0.0.1 --port 8000
```

`python web_dashboard.py` binds `0.0.0.0:8000` (all interfaces); prefer the command above on a normal machine.
Railway uses `uvicorn web_dashboard:app --host 0.0.0.0 --port $PORT` (`railway.json`). A `Dockerfile` and
`docker-compose.yml` exist; `DOCKER_README.md` has the details.

## Tests and CI

```bash
python -m pytest -q                       # no network, no keys needed
flake8 . --count --select=E9,F63,F7,F82   # the fatal lint gate: syntax errors and undefined names
```

`tests/conftest.py` blocks outbound connections, ignores any local `.env` and sets dummy provider keys, so a test can never
reach a real provider, Redis or webhook. GitHub Actions (`.github/workflows/`) runs the suite on Python 3.11, 3.12 and 3.13 plus
the lint gate. The wider flake8 style report is informational and not clean.

## Layout

| Path | What |
|---|---|
| `main.py` | interactive menu and the mode runners |
| `ai_framework.py` | providers, the async message bus, persistence (Redis with SQLite fallback), TOON/JSON encoding |
| `base.py` | Pantheon agent base class and the shared AI provider bus |
| `src/agents/` | Observer, Reasoner, Actor, Memory, Validator, Learner, Analyzer, Executor, Improver and more |
| `src/oram.py` | ORAM iterative loop |
| `src/decision_gate.py`, `docs/decision_gate.md` | optional local "Clef" decision-gate router for `send_message` (off by default) |
| `src/mcp_servers/`, `config/mcp_servers.json` | MCP server integrations |
| `web_dashboard.py`, `templates/`, `static/` | FastAPI dashboard |
| `tests/` | offline pytest suite |

Many `*.md` files in the root (`PHASE2_COMPLETE.md` and similar) are old session notes, not documentation. `foundation.md` is a story.

## License

MIT, see `LICENSE`.
