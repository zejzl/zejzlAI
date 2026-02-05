#!/usr/bin/env python3
"""
Test script for xAI Grok API integration
Verifies that the GrokProvider correctly calls the xAI API
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

from ai_framework import GrokProvider
from src.cost_calculator import TokenUsage


async def test_grok_api():
    """Test the Grok API with a simple query"""
    print("=" * 60)
    print("Testing xAI Grok API Integration")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        print("❌ ERROR: GROK_API_KEY not found in .env file")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-10:]}")
    
    # Initialize provider
    print("\n📡 Initializing GrokProvider...")
    provider = GrokProvider(
        api_key=api_key,
        model="grok-2-1212"  # Default model
    )
    
    await provider.initialize()
    print(f"✓ Provider initialized with model: {provider.model}")
    
    # Test message
    test_message = "Hello! Please respond with a single sentence confirming you are Grok from xAI."
    print(f"\n💬 Sending test message: '{test_message}'")
    
    try:
        # Generate response
        print("⏳ Waiting for response...")
        response, token_usage = await provider.generate_response(test_message)
        
        # Display results
        print("\n" + "=" * 60)
        print("✅ SUCCESS! API Response:")
        print("=" * 60)
        print(f"\n📝 Response:\n{response}\n")
        print("=" * 60)
        print("📊 Token Usage:")
        print("=" * 60)
        print(f"   Provider: {token_usage.provider}")
        print(f"   Model: {token_usage.model}")
        print(f"   Prompt Tokens: {token_usage.prompt_tokens}")
        print(f"   Completion Tokens: {token_usage.completion_tokens}")
        print(f"   Total Tokens: {token_usage.total_tokens}")
        print(f"   Cost: ${token_usage.cost:.6f}")
        print("=" * 60)
        
        # Cleanup
        await provider.cleanup()
        print("\n✓ Provider cleanup complete")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR during API call:")
        print("=" * 60)
        print(f"   {type(e).__name__}: {str(e)}")
        print("=" * 60)
        
        # Cleanup even on error
        await provider.cleanup()
        
        return False


async def test_grok_streaming():
    """Test Grok API streaming response"""
    print("\n" + "=" * 60)
    print("🧪 Testing xAI Grok Streaming API")
    print("=" * 60)
    
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        print("❌ ERROR: GROK_API_KEY not found")
        return False
    
    provider = GrokProvider(api_key=api_key, model="grok-2-1212")
    await provider.initialize()
    
    test_message = "Count from 1 to 5, one number per line."
    print(f"\n💬 Streaming test message: '{test_message}'")
    print("⏳ Streaming response:\n")
    
    try:
        full_response = ""
        async for chunk in provider.generate_response_stream(test_message):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print("\n\n" + "=" * 60)
        print("✅ Streaming test complete!")
        print(f"   Total characters received: {len(full_response)}")
        print("=" * 60)
        
        await provider.cleanup()
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming error: {type(e).__name__}: {str(e)}")
        await provider.cleanup()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Grok API Integration Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Basic API call
    test1_result = await test_grok_api()
    
    # Test 2: Streaming API call
    test2_result = await test_grok_streaming()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    print(f"   Basic API:     {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Streaming API: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Grok API integration is working!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
