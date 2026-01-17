#!/usr/bin/env python3
"""
Test script for Enterprise Security & Encryption in ZEJZL.NET

Demonstrates end-to-end encryption capabilities and secure communications.
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.security import EnterpriseSecurity

async def demo():
    """Demonstrate enterprise security features"""
    print("Enterprise Security Demo")
    print("=" * 40)

    try:
        # Initialize security
        security = EnterpriseSecurity(enable_encryption=True)
        await security.initialize_security()

        # Test encryption
        engine = security.encryption_engine

        test_data = {"message": "Hello, secure world!", "timestamp": "2024-01-17T12:00:00Z"}
        print(f"Original data: {test_data}")

        # Encrypt
        encrypted = engine.encrypt_json(test_data)
        print(f"Encrypted length: {len(encrypted)} characters")

        # Decrypt
        decrypted = engine.decrypt_json(encrypted)
        print(f"Decrypted: {decrypted}")

        # Verify round-trip
        assert decrypted == test_data, "Encryption/decryption failed!"
        print("+ Round-trip encryption successful")

        # Key management
        current_key = security.key_manager.get_current_key()
        print(f"Current key ID: {current_key['key_id'] if current_key else 'None'}")

        # Rotate key
        old_key = current_key['key_id'] if current_key else None
        new_key = await security.rotate_keys()
        print(f"Key rotated from {old_key} to {new_key}")

        # Security status
        status = security.get_security_status()
        print(f"Security status: {status}")

        print("Enterprise security demo complete!")

    except Exception as e:
        print(f"ERROR: Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo())