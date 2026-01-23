#!/usr/bin/env python3
"""
Test Pantheon Mode with Gemini
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from main import run_pantheon_mode

async def test_pantheon_gemini():
    """Test Pantheon mode with Gemini provider"""

    # Mock the input for testing
    import builtins
    original_input = builtins.input

    inputs = iter([
        "gemini",  # Provider selection
        "Write me a haiku about artificial intelligence",  # Task
        "n"  # Don't run another task
    ])

    def mock_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            return "n"  # Default to no

    builtins.input = mock_input

    try:
        print("Testing Pantheon Mode with Gemini...")
        await run_pantheon_mode()
        print("Pantheon Mode test completed!")
    finally:
        builtins.input = original_input

if __name__ == "__main__":
    asyncio.run(test_pantheon_gemini())