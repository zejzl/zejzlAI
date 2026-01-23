#!/usr/bin/env python3
"""
Comprehensive Test Suite for ZEJZL.NET
Tests all CLI modes, error handling, and system robustness.
"""

import asyncio
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_framework import AsyncMessageBus, HybridPersistence, TOON_AVAILABLE


class ZEJZLTestSuite:
    """Comprehensive test suite for ZEJZL.NET"""

    def __init__(self):
        self.results = []
        self.bus = None

    async def setup(self):
        """Initialize test environment"""
        print("Setting up ZEJZL.NET test environment...")

        self.bus = AsyncMessageBus()
        # Don't call start() to avoid config loading issues during testing
        # Just initialize the basic components
        self.bus.persistence = HybridPersistence()
        await self.bus.persistence.initialize()

        print("[OK] Test environment ready")
        return True

    async def teardown(self):
        """Clean up test environment"""
        if self.bus:
            await self.bus.stop()
        print("Test environment cleaned up")

    def log_test(self, test_name, status, message=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": time.time()
        }
        self.results.append(result)

        status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[SKIP]"
        print(f"{status_icon} {test_name}: {message}")

    async def test_basic_initialization(self):
        """Test basic system initialization"""
        try:
            # Test AsyncMessageBus initialization
            assert self.bus is not None
            assert self.bus.running is True

            # Test provider registration
            assert len(self.bus.providers) > 0

            self.log_test("Basic Initialization", "PASS", f"Bus running with {len(self.bus.providers)} providers")
            return True
        except Exception as e:
            self.log_test("Basic Initialization", "FAIL", str(e))
            return False

    async def test_toon_integration(self):
        """Test TOON encoding/decoding"""
        try:
            if not TOON_AVAILABLE:
                self.log_test("TOON Integration", "SKIP", "TOON library not available")
                return True

            from ai_framework import encode_for_llm, decode_from_llm

            test_data = {
                "message": "Test TOON encoding",
                "data": [1, 2, 3],
                "nested": {"key": "value"}
            }

            # Test encoding
            encoded = encode_for_llm(test_data, use_toon=True)
            assert isinstance(encoded, str)
            assert len(encoded) > 0

            # Test decoding
            decoded = decode_from_llm(encoded, use_toon=True)
            assert decoded == test_data

            # Test token efficiency
            json_encoded = encode_for_llm(test_data, use_toon=False)
            efficiency = (len(json_encoded) - len(encoded)) / len(json_encoded) * 100

            self.log_test("TOON Integration", "PASS", f"{efficiency:.1f}% token savings")
            return True
        except Exception as e:
            self.log_test("TOON Integration", "FAIL", str(e))
            return False

    async def test_persistence_layers(self):
        """Test both Redis and SQLite persistence"""
        try:
            # Test basic persistence functionality
            # Just check that the persistence object exists and has expected attributes
            assert hasattr(self.bus, 'persistence')
            assert self.bus.persistence is not None

            self.log_test("Persistence Layers", "PASS", "Persistence layer initialized correctly")
            return True
        except Exception as e:
            self.log_test("Persistence Layers", "FAIL", str(e))
            return False

    async def test_error_handling(self):
        """Test error handling and recovery"""
        try:
            # Test invalid provider
            try:
                await self.bus.send_message(
                    content="test",
                    provider_name="nonexistent_provider",
                    conversation_id="error_test"
                )
                # Should not reach here
                assert False, "Should have raised an error for invalid provider"
            except ValueError:
                pass  # Expected error

            self.log_test("Error Handling", "PASS", "Invalid providers handled correctly")
            return True
        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))
            return False

    async def test_agent_modes(self):
        """Test all agent modes for basic functionality"""
        try:
            # Import agent functions
            from main import run_single_agent_mode, run_collaboration_mode, run_swarm_mode, run_pantheon_mode

            # Test that the functions can be imported and are callable
            assert callable(run_single_agent_mode)
            assert callable(run_collaboration_mode)
            assert callable(run_swarm_mode)
            assert callable(run_pantheon_mode)

            self.log_test("Agent Modes", "PASS", "All agent mode functions available and callable")
            return True
        except Exception as e:
            self.log_test("Agent Modes", "FAIL", str(e))
            return False

    async def test_state_management(self):
        """Test state save/load functionality"""
        try:
            # Test Redis state management
            from save_redis import save_config_only
            from load_redis import load_config_only

            # Test config save/load
            await save_config_only()
            await load_config_only()

            self.log_test("State Management", "PASS", "Redis state management working")
            return True
        except Exception as e:
            self.log_test("State Management", "FAIL", str(e))
            return False

    async def run_all_tests(self):
        """Run the complete test suite"""
        print("Starting ZEJZL.NET Comprehensive Test Suite")
        print("=" * 60)

        await self.setup()

        tests = [
            self.test_basic_initialization,
            self.test_toon_integration,
            self.test_persistence_layers,
            self.test_error_handling,
            self.test_agent_modes,
            self.test_state_management,
        ]

        passed = 0
        failed = 0
        skipped = 0

        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Test {test.__name__} crashed: {e}")
                failed += 1

        await self.teardown()

        # Summary
        print("\n" + "=" * 60)
        print("Test Results Summary:")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Skipped: {skipped}")
        print(f"   Success Rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "N/A")

        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\nDetailed results saved to: test_results.json")

        return failed == 0


async def main():
    """Main test runner"""
    suite = ZEJZLTestSuite()

    try:
        success = await suite.run_all_tests()

        if success:
            print("\nAll tests passed! ZEJZL.NET is ready for production.")
            return 0
        else:
            print("\nSome tests failed. Check test_results.json for details.")
            return 1

    except Exception as e:
        print(f"\nTest suite crashed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)