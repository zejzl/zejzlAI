# AGENTS.md (zejzlAI)

For any AI agent working in this repo. Owner: Zejzl. Read `README.md` first for how to run and test it.

## Hard rules
- No secrets: never print, commit or paste API keys, `.env` values, or the contents of the `.db` files. `.env`, `*.db` and logs are git-ignored; keep it that way. Saved config must not contain keys.
- Tests must stay offline. `tests/conftest.py` blocks network and sets dummy keys; do not weaken it. Fake the provider bus (`base.get_ai_provider_bus`) as `tests/test_agent_fallbacks.py` does.
- The fatal lint gate must stay clean: `flake8 . --select=E9,F63,F7,F82`. The full style report is not clean and is not required.
- Do not touch `~/Projects/zejzlAI-neo`. It is Neo's git worktree (branch `neo/clef-router`).
- Coordinate through `~/Projects/WORKING.md` (claim a line before editing, mark it done after) and the neo-mailbox `BOARD.md`.

## Git
- Work on a branch off `main`; open a PR; never push to `main` directly.
- Zejzl's rule for every repo (`~/CLAUDE.md`, Git section): agents may merge green PRs that another agent reviewed, **except** repos that deploy to production on merge. zejzlAI is on that list, so **merging here needs Zejzl's yes**.
- Never force-push or rewrite history.

## Working in the code
- Python style: PEP 8, type hints where cheap, no emojis in source (the CLI is used on Windows consoles too). Console output tags: `[OK]`, `[WARNING]`, `[ERROR]`, `[INFO]`.
- Agents call providers via `send_message(content, provider_name, conversation_id)` on the shared bus. If a call fails they must degrade to a rule-based answer and mark it (`ai_generated: False`, with `fallback_reason` or `error`), never raise to the caller.
- ORAM (`src/oram.py`): the current iteration is not in `iteration_history` until after convergence is checked; keep that in mind when touching `_check_convergence` or `_extract_insights`. Known quirks, not fixed: the insight "previous iteration" lookup uses `[-2]`, and the declining-trend check ignores the current score.
- Models and provider names change often. When updating a default model, change it in `ai_framework.py`, `README.md` and the related test in `tests/test_providers.py` together.
- `main.py` and `ai_framework.py` are large. Prefer small, tested changes over refactors unless asked.

## Before opening a PR
```bash
python -m pytest -q
flake8 . --count --select=E9,F63,F7,F82
```
Say in the PR what you ran, and what you did not run (for example live provider calls).
