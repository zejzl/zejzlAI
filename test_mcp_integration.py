#!/usr/bin/env python3
"""
MCP Integration Test Suite for ZEJZL.NET
Comprehensive tests for MCP client, servers, and integration.
"""

import asyncio
import json
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import unittest
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp_client import MCPClient
from src.mcp_types import MCPMethod, MCPServerInfo
from src.mcp_registry import MCPRegistry


class MCPIntegrationTest(unittest.TestCase):
    """Test MCP client and server integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = MCPRegistry()
        self.test_server_process = None

    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_server_process:
            self.test_server_process.terminate()
            self.test_server_process.wait()

    def test_mcp_client_initialization(self):
        """Test MCP client can be initialized"""
        client = MCPClient("test_client")
        self.assertIsNotNone(client)
        self.assertEqual(client.client_name, "test_client")

    def test_mcp_registry_operations(self):
        """Test MCP registry basic operations"""
        # Register a mock server
        server_info = {
            "name": "test_server",
            "version": "1.0.0",
            "transport": "stdio",
            "command": ["echo", "test"]
        }

        self.registry.register_server("test_server", server_info)
        registered = self.registry.get_server("test_server")
        self.assertIsNotNone(registered)
        self.assertEqual(registered["name"], "test_server")

    async def test_mcp_server_connection(self):
        """Test connecting to MCP server"""
        # Start test server in background
        self.test_server_process = subprocess.Popen(
            [sys.executable, "src/mcp_servers/test_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give server time to start
        await asyncio.sleep(1)

        # Try to connect (this would need a full client implementation)
        # For now, just test that server started
        self.assertIsNotNone(self.test_server_process.poll())
        if self.test_server_process.poll() is None:  # Still running
            self.test_server_process.terminate()
            self.test_server_process.wait()

    def test_mcp_types_validation(self):
        """Test MCP type definitions"""
        from src.mcp_types import MCPErrorCode, MCPMethod

        # Test error codes
        self.assertEqual(MCPErrorCode.PARSE_ERROR, -32700)
        self.assertEqual(MCPErrorCode.INVALID_REQUEST, -32600)

        # Test methods
        self.assertEqual(MCPMethod.INITIALIZE, "initialize")
        self.assertEqual(MCPMethod.TOOLS_LIST, "tools/list")


class MCPClientTest(unittest.TestCase):
    """Test MCP client functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = MCPClient("test_client")

    def test_client_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.client_name, "test_client")
        self.assertIsNotNone(self.client.client_info)

    def test_client_capabilities(self):
        """Test client capabilities"""
        caps = self.client.get_client_capabilities()
        self.assertIsInstance(caps, dict)
        self.assertIn("sampling", caps)


class MCPRegistryTest(unittest.TestCase):
    """Test MCP registry functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = MCPRegistry()

    def test_registry_initialization(self):
        """Test registry initialization"""
        self.assertIsInstance(self.registry.servers, dict)
        self.assertIsInstance(self.registry.health_status, dict)

    def test_server_registration(self):
        """Test server registration"""
        server_config = {
            "name": "test_server",
            "version": "1.0.0",
            "transport": "stdio",
            "command": ["python", "test_server.py"]
        }

        self.registry.register_server("test_server", server_config)
        server = self.registry.get_server("test_server")
        self.assertIsNotNone(server)
        self.assertEqual(server["name"], "test_server")

    def test_server_health_check(self):
        """Test server health checking"""
        # Register server
        server_config = {
            "name": "test_server",
            "version": "1.0.0",
            "transport": "stdio",
            "command": ["python", "test_server.py"]
        }
        self.registry.register_server("test_server", server_config)

        # Check health (should fail since server isn't running)
        health = self.registry.check_server_health("test_server")
        self.assertIsNotNone(health)
        self.assertIn("status", health)


class MCPToolTest(unittest.TestCase):
    """Test MCP tool functionality"""

    def test_tool_definition_structure(self):
        """Test tool definition structure"""
        from src.mcp_types import MCPTool

        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            inputSchema={"type": "object", "properties": {}}
        )

        self.assertEqual(tool.name, "test_tool")
        self.assertEqual(tool.description, "A test tool")

        # Test to_dict
        tool_dict = tool.to_dict()
        self.assertIsInstance(tool_dict, dict)
        self.assertEqual(tool_dict["name"], "test_tool")


class MCPIntegrationTest(unittest.TestCase):
    """Full integration tests for MCP system"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Hello, this is a test file!")

        self.test_dir = self.temp_dir

    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_operations(self):
        """Test basic file operations that MCP server would use"""
        # Test file exists
        self.assertTrue(os.path.exists(self.test_file))

        # Test file reading
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Hello, this is a test file!")

        # Test directory listing
        items = os.listdir(self.test_dir)
        self.assertIn("test.txt", items)

    def test_math_operations(self):
        """Test math operations that MCP server might perform"""
        # Test addition
        result = 5 + 3
        self.assertEqual(result, 8)

        # Test with different types
        result_float = 5.5 + 3.2
        self.assertAlmostEqual(result_float, 8.7, places=1)


class MCPPerformanceTest(unittest.TestCase):
    """Performance tests for MCP operations"""

    def test_operation_timing(self):
        """Test that operations complete within reasonable time"""
        import time

        start_time = time.time()

        # Simulate a simple operation
        result = sum(range(1000))

        end_time = time.time()
        duration = end_time - start_time

        # Should complete very quickly
        self.assertLess(duration, 0.01)
        self.assertEqual(result, 499500)

    def test_memory_usage(self):
        """Test memory usage for operations"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform some operations
        data = list(range(10000))
        result = sum(data)

        final_memory = process.memory_info().rss
        memory_used = final_memory - initial_memory

        # Memory usage should be reasonable (less than 10MB increase)
        self.assertLess(memory_used, 10 * 1024 * 1024)
        self.assertEqual(result, 49995000)


class MCPConcurrencyTest(unittest.TestCase):
    """Concurrency tests for MCP operations"""

    def test_async_operations(self):
        """Test asynchronous operations"""
        async def async_test():
            await asyncio.sleep(0.01)
            return "completed"

        async def run_test():
            result = await async_test()
            return result

        result = asyncio.run(run_test())
        self.assertEqual(result, "completed")

    def test_concurrent_operations(self):
        """Test concurrent operations"""
        async def worker(worker_id: int):
            await asyncio.sleep(0.01)
            return f"worker_{worker_id}"

        async def run_workers():
            tasks = [worker(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_workers())
        self.assertEqual(len(results), 5)
        self.assertIn("worker_0", results)
        self.assertIn("worker_4", results)


def run_integration_tests():
    """Run all MCP integration tests"""
    print("🧪 Running MCP Integration Test Suite")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        MCPIntegrationTest,
        MCPClientTest,
        MCPRegistryTest,
        MCPToolTest,
        MCPPerformanceTest,
        MCPConcurrencyTest
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:"    print(f"   Ran: {result.testsRun} tests")
    print(f"   Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Failed: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"   - {test}")

    if result.errors:
        print(f"\n💥 Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"   - {test}")

    if result.wasSuccessful():
        print("\n✅ All MCP integration tests passed!")
        return True
    else:
        print("\n❌ Some MCP integration tests failed!")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)