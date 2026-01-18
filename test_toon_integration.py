#!/usr/bin/env python3
"""
TOON Integration Test for ZEJZL.NET
Tests token-efficient agent communications using TOON format.
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_toon_integration():
    """Test TOON encoding/decoding functionality"""

    # Sample agent communication data
    test_data = {
        "objective": "Analyze AI news trends",
        "requirements": [
            "Gather recent AI developments",
            "Identify key trends and patterns",
            "Assess market impact"
        ],
        "complexity_level": "Medium",
        "estimated_effort": "High",
        "stakeholders": [
            {"role": "analyst", "priority": "high"},
            {"role": "executive", "priority": "medium"}
        ]
    }

    print("Testing TOON Integration for ZEJZL.NET")
    print("=" * 60)

    # Test TOON availability
    try:
        from ai_framework import TOON_AVAILABLE, encode_for_llm, decode_from_llm
        print(f"TOON Available: {TOON_AVAILABLE}")

        if TOON_AVAILABLE:
            # Test encoding
            toon_encoded = encode_for_llm(test_data, use_toon=True)
            json_encoded = encode_for_llm(test_data, use_toon=False)

            print("\nToken Efficiency Comparison:")
            print(f"TOON Length: {len(toon_encoded)} chars")
            print(f"JSON Length: {len(json_encoded)} chars")
            savings = ((len(json_encoded) - len(toon_encoded)) / len(json_encoded)) * 100
            print(f"Token Savings: {savings:.1f}%")
            print(f"\nTOON Format:\n{toon_encoded}")
            print(f"\nJSON Format:\n{json_encoded}")

            # Test decoding
            decoded = decode_from_llm(toon_encoded, use_toon=True)
            print(f"\nDecoded successfully: {decoded == test_data}")

        else:
            print("TOON not available. Install with: pip install toon_format")

    except ImportError as e:
        print(f"Import Error: {e}")
        return False

    print("\nTOON Integration Test Complete!")
    return True

if __name__ == "__main__":
    test_toon_integration()