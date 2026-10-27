"""SQLite persistence in ai_framework against a temporary database file."""

import asyncio
from datetime import datetime, timedelta

import ai_framework


def _message(i, conversation="conv", response=None):
    return ai_framework.Message(
        id=f"m{i}",
        content=f"question {i}",
        timestamp=datetime(2026, 1, 1, 12, 0) + timedelta(seconds=i),
        sender="tester",
        provider="grok",
        response=response,
        conversation_id=conversation,
    )


def test_sqlite_save_and_history(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    async def scenario():
        store = ai_framework.SQLitePersistence(db_path=str(tmp_path / "test.db"))
        await store.initialize()
        try:
            await store.save_message(_message(1, response="answer 1"))
            await store.save_message(_message(2, response="answer 2"))
            await store.save_message(_message(3))  # no response: not in history
            await store.save_message(_message(4, conversation="other", response="x"))
            return await store.get_conversation_history("conv", limit=10)
        finally:
            await store.cleanup()

    history = asyncio.run(scenario())
    assert history == [
        {"role": "user", "content": "question 1"},
        {"role": "assistant", "content": "answer 1"},
        {"role": "user", "content": "question 2"},
        {"role": "assistant", "content": "answer 2"},
    ]
