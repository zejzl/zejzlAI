"""F14: model/agent code must run in a genuinely terminable subprocess.

Before this fix, ExecutorAgent._execute_code_step ran code with exec() in the
current process. Its `timeout` parameter was accepted but never enforced, so
a runaway/infinite-loop snippet hung forever and could block the whole
process. These tests prove: (1) the timeout actually kills a hanging
subprocess within a bounded wall-clock time, so the test suite itself never
hangs, and (2) a normal, fast snippet still runs to completion and reports
success.
"""

import asyncio
import time

import pytest

from src.agents.executor import ExecutorAgent


@pytest.mark.asyncio
async def test_infinite_loop_is_killed_at_timeout():
    """A `while True: pass` snippet must be killed, not hang the suite."""
    executor = ExecutorAgent()
    step = {
        "type": "code",
        "language": "python",
        "code": "while True:\n    pass\n",
        "timeout": 1,
    }

    started = time.monotonic()
    # asyncio.wait_for here is a second, independent safety net: if the fix
    # regressed and the subprocess timeout stopped being enforced, this test
    # itself fails fast instead of hanging the whole suite.
    result = await asyncio.wait_for(executor._execute_step(step, 1, 1), timeout=10)
    elapsed = time.monotonic() - started

    assert result["status"] == "failed"
    assert "timed out" in result["message"].lower()
    # Generous bound: the subprocess timeout is 1s, give scheduling slack,
    # but it must be far below the old "never enforced" (effectively forever).
    assert elapsed < 5, f"runaway code step took {elapsed:.2f}s, timeout was not enforced"


@pytest.mark.asyncio
async def test_code_step_runs_out_of_process_and_succeeds():
    """A normal snippet still runs to completion and is marked a subprocess run."""
    executor = ExecutorAgent()
    step = {
        "type": "code",
        "language": "python",
        "code": "print('hello from subprocess')",
        "timeout": 5,
    }

    result = await executor._execute_step(step, 1, 1)

    assert result["status"] == "success"
    assert result["execution_environment"] == "subprocess"
    assert "hello from subprocess" in result["output"]


@pytest.mark.asyncio
async def test_code_step_reports_failure_for_bad_code():
    """Code that raises still returns a failed result, not an exception."""
    executor = ExecutorAgent()
    step = {
        "type": "code",
        "language": "python",
        "code": "raise ValueError('boom')",
        "timeout": 5,
    }

    result = await executor._execute_step(step, 1, 1)

    assert result["status"] == "failed"
    assert "boom" in result["message"]
