#!/usr/bin/env python3
"""Simple test for xAI Grok API integration"""

import asyncio
import os
import sys
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

from ai_framework import GrokProvider


async def test_grok():
    print("\n" + "=" * 60)
    print("Testing xAI Grok API Integration")
    print("=" * 60)
    
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        print("ERROR: GROK_API_KEY not found in .env file")
        return False
    
    print(f"API Key: {api_key[:15]}...{api_key[-10:]}")
    
    provider = GrokProvider(api_key=api_key, model="grok-4-fast-reasoning")
    await provider.initialize()
    print(f"Provider initialized: {provider.name} ({provider.model})")
    
    test_message = "Hello! Please respond with one sentence confirming you are Grok."
    print(f"\nSending: '{test_message}'")
    print("Waiting for response...\n")
    
    try:
        response, token_usage = await provider.generate_response(test_message)
        
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nResponse:\n{response}\n")
        print("=" * 60)
        print("Token Usage:")
        print(f"  Provider: {token_usage.provider}")
        print(f"  Model: {token_usage.model}")
        print(f"  Prompt tokens: {token_usage.prompt_tokens}")
        print(f"  Completion tokens: {token_usage.completion_tokens}")
        print(f"  Total: {token_usage.total_tokens}")
        print("=" * 60)
        
        await provider.cleanup()
        return True
        
    except Exception as e:
        print("=" * 60)
        print("ERROR:")
        print("=" * 60)
        print(f"{type(e).__name__}: {str(e)}")
        print("=" * 60)
        await provider.cleanup()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_grok())
    if result:
        print("\nTest PASSED! Grok API integration is working!\n")
    else:
        print("\nTest FAILED. Check the error above.\n")
