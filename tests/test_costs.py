"""Cost calculator, budget alert thresholds and the rate limiter token bucket."""

import asyncio

import pytest

from rate_limiter import TokenBucket
from src.budget_alerts import BudgetAlertManager
from src.cost_calculator import CostCalculator, TokenUsage


def test_total_tokens_filled_in():
    usage = TokenUsage(provider="chatgpt", model="gpt-4", prompt_tokens=10, completion_tokens=5)
    assert usage.total_tokens == 15
    assert usage.timestamp is not None


def test_known_model_cost():
    # gpt-4: 0.03 in / 0.06 out per 1K tokens
    cost = CostCalculator.estimate_cost("ChatGPT", "GPT-4", 1000, 1000)
    assert cost == pytest.approx(0.09)


def test_cost_written_back_to_usage():
    usage = TokenUsage(provider="chatgpt", model="gpt-3.5-turbo", prompt_tokens=2000, completion_tokens=500)
    cost = CostCalculator.calculate_cost(usage)
    assert usage.cost_usd == cost == pytest.approx(0.004)


def test_partial_model_match():
    pricing = CostCalculator.get_provider_pricing("gemini", "gemini-2.5-flash-latest")
    assert pricing == {"input": 0.00015, "output": 0.0006}


def test_unknown_provider_uses_default():
    assert CostCalculator.get_provider_pricing("nobody", "x") == {"input": 0.01, "output": 0.02}
    assert CostCalculator.estimate_cost("nobody", "x", 1000, 1000) == pytest.approx(0.03)


def test_zero_tokens_cost_nothing():
    assert CostCalculator.estimate_cost("grok", "grok-1", 0, 0) == 0


@pytest.mark.parametrize(
    "used,limit,level",
    [
        (0, 100, None),
        (79, 100, None),
        (80, 100, "WARNING"),
        (90, 100, "CRITICAL"),
        (100, 100, "EXHAUSTED"),
        (150, 100, "EXHAUSTED"),
    ],
)
def test_budget_alert_levels(tmp_path, used, limit, level):
    manager = BudgetAlertManager(discord_webhook_url=None, data_dir=tmp_path)
    assert manager.get_alert_level(manager.calculate_percentage(used, limit)) == level


def test_budget_zero_limit(tmp_path):
    manager = BudgetAlertManager(discord_webhook_url=None, data_dir=tmp_path)
    assert manager.calculate_percentage(5, 0) == 0.0


def test_budget_alert_dedup(tmp_path):
    manager = BudgetAlertManager(discord_webhook_url=None, data_dir=tmp_path)
    assert manager.should_send_alert("task-1", "WARNING")
    manager.mark_alert_sent("task-1", "WARNING")
    assert not manager.should_send_alert("task-1", "WARNING")
    assert manager.should_send_alert("task-1", "CRITICAL")
    assert manager.should_send_alert("task-2", "WARNING")


def test_token_bucket_limits_burst():
    async def scenario():
        bucket = TokenBucket(capacity=2, refill_rate=0.001)
        first = await bucket.acquire(timeout=0.05)
        second = await bucket.acquire(timeout=0.05)
        third = await bucket.acquire(timeout=0.05)
        return first, second, third

    assert asyncio.run(scenario()) == (True, True, False)
