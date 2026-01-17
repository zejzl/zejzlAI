#!/usr/bin/env python3
"""
Test script for Advanced AI Capabilities in ZEJZL.NET
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.advanced_ai import process_natural_language, perform_advanced_reasoning, orchestrate_ai_models, ModalityType

async def demo():
    """Demonstrate advanced AI capabilities"""
    print("Advanced AI Capabilities Demo")
    print("=" * 50)

    try:
        # Test natural language processing
        print("\nTesting Natural Language Processing...")
        text = "Create a Python function to analyze sales data"
        nlp_result = await process_natural_language(text)
        print(f"  Intent: {nlp_result['intent']['primary_intent']}")
        print(f"  Confidence: {nlp_result['intent']['confidence']}")
        print(f"  Word Count: {nlp_result['complexity']['word_count']}")

        # Test advanced reasoning
        print("\nTesting Advanced Reasoning...")
        reasoning_result = await perform_advanced_reasoning(text)
        print(f"  Strategy: {reasoning_result['step']['strategy']['value']}")
        print(f"  Conclusion: {reasoning_result['result']['conclusion'][:50]}...")

        # Test AI model orchestration
        print("\nTesting AI Model Orchestration...")
        orchestration_result = await orchestrate_ai_models(text, ModalityType.TEXT)
        print(f"  Models Used: {orchestration_result['model_sequence']}")
        print(f"  Output: {orchestration_result['final_output'][:50]}...")

        print("\nAdvanced AI capabilities demonstration complete!")

    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(demo())