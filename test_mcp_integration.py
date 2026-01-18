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
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp_client import MCPClient, MCPConnectionError, MCPProtocolError, MCPTimeoutError
from src.mcp_types import MCPMethod, MCPServerInfo, MCPTransport
from src.mcp_registry import MCPServerRegistry
from src.mcp_agent_integration import MCPAgentInterface
from src.mcp_security import get_security_manager


class MCPMockServerTest(unittest.TestCase):
    """Test MCP client with mock servers"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_server_process = None

    def tearDown(self):
        """Clean up test fixtures"""
        if self.mock_server_process:
            try:
                self.mock_server_process.terminate()
                self.mock_server_process.wait(timeout=5)
            except:
                self.mock_server_process.kill()

        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def start_mock_server(self):
        """Start the mock MCP server"""
        cmd = [sys.executable, "mock_mcp_server.py", "stdio"]
        self.mock_server_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        # Give server time to start
        time.sleep(0.5)

    async def test_stdio_server_connection(self):
        """Test connecting to mock stdio server"""
        self.start_mock_server()

        # Create client
        client = MCPClient(
            server_name="mock_server",
            transport=MCPTransport.STDIO,
            command=[sys.executable, "mock_mcp_server.py", "stdio"],
            timeout=10.0
        )

        try:
            # Connect and get server info
            server_info = await client.connect()
            self.assertIsNotNone(server_info)
            self.assertEqual(server_info.name, "mock_stdio_server")

            # Test tools listing
            tools = await client.list_tools()
            self.assertIsInstance(tools, list)
            self.assertGreater(len(tools), 0)

            tool_names = [t.name for t in tools]
            self.assertIn("echo", tool_names)
            self.assertIn("add_numbers", tool_names)

            # Test tool calling
            result = await client.call_tool("echo", {"message": "hello world"})
            self.assertEqual(result, {"echoed": "hello world"})

            result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
            self.assertEqual(result, {"sum": 8})

            # Test resources listing
            resources = await client.list_resources()
            self.assertIsInstance(resources, list)
            self.assertGreater(len(resources), 0)

            # Test resource reading
            resource_uris = [r.uri for r in resources]
            self.assertIn("file:///tmp/mock_data.txt", resource_uris)

            content = await client.read_resource("file:///tmp/mock_data.txt")
            self.assertIn("mock data", content["contents"][0]["text"].lower())

        finally:
            await client.disconnect()

    async def test_client_error_handling(self):
        """Test client error handling"""
        self.start_mock_server()

        client = MCPClient(
            server_name="mock_server",
            transport=MCPTransport.STDIO,
            command=[sys.executable, "mock_mcp_server.py", "stdio"],
            timeout=10.0
        )

        try:
            await client.connect()

            # Test calling non-existent tool
            with self.assertRaises(MCPProtocolError):
                await client.call_tool("nonexistent_tool", {})

            # Test reading non-existent resource
            with self.assertRaises(MCPProtocolError):
                await client.read_resource("file:///nonexistent.txt")

        finally:
            await client.disconnect()

    async def test_client_timeout_handling(self):
        """Test client timeout handling"""
        # Create client with very short timeout
        client = MCPClient(
            server_name="slow_server",
            transport=MCPTransport.STDIO,
            command=[sys.executable, "-c", "import time; time.sleep(10)"],  # Slow command
            timeout=0.1
        )

        with self.assertRaises(MCPTimeoutError):
            await client.connect()


class MCPRegistryIntegrationTest(unittest.TestCase):
    """Test MCP registry integration"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock magic system that doesn't start async tasks
        class MockMagic:
            energy_level = 100
            async def auto_heal(self, *args, **kwargs):
                return False

        self.registry = MCPServerRegistry(magic_system=MockMagic())
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_registry_initialization(self):
        """Test registry initialization"""
        self.assertIsInstance(self.registry.configs, dict)
        self.assertIsInstance(self.registry.status, dict)

    async def test_registry_with_mock_server(self):
        """Test registry with mock server config"""
        # Create temporary config file
        config_path = os.path.join(self.temp_dir, "test_config.json")
        config_data = {
            "version": "1.0",
            "servers": [{
                "name": "test_mock_server",
                "transport": "stdio",
                "command": [sys.executable, "mock_mcp_server.py", "stdio"],
                "enabled": True,
                "timeout": 10.0,
                "auto_reconnect": False
            }]
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        # Load config
        await self.registry.load_config(Path(config_path))

        # Check server was loaded
        self.assertIn("test_mock_server", self.registry.configs)
        config = self.registry.configs["test_mock_server"]
        self.assertEqual(config.transport, "stdio")

    async def test_registry_server_management(self):
        """Test registry server management"""
        from src.mcp_registry import MCPServerConfig

        # Create server config
        config = MCPServerConfig(
            name="managed_server",
            transport="stdio",
            command=[sys.executable, "mock_mcp_server.py", "stdio"],
            enabled=True
        )

        # Register server
        success = await self.registry.register_server(config)
        self.assertTrue(success)
        self.assertIn("managed_server", self.registry.configs)

        # Unregister server
        success = await self.registry.unregister_server("managed_server")
        self.assertTrue(success)
        self.assertNotIn("managed_server", self.registry.configs)


class MCPAgentIntegrationTest(unittest.TestCase):
    """Test MCP agent integration layer"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock magic system that doesn't start async tasks
        class MockMagic:
            energy_level = 100
            async def auto_heal(self, *args, **kwargs):
                return False

        self.registry = MCPServerRegistry(magic_system=MockMagic())
        self.agent_interface = MCPAgentInterface(self.registry)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_interface_initialization(self):
        """Test agent interface initialization"""
        self.assertIsInstance(self.agent_interface.registry, MCPServerRegistry)
        self.assertIsInstance(self.agent_interface.contexts, dict)

    def test_agent_context_management(self):
        """Test agent context management"""
        context = self.agent_interface.get_context("test_agent", "session_1")
        self.assertEqual(context.agent_name, "test_agent")
        self.assertEqual(context.session_id, "session_1")

        # Get same context again
        context2 = self.agent_interface.get_context("test_agent", "session_1")
        self.assertEqual(context, context2)

        # Different session
        context3 = self.agent_interface.get_context("test_agent", "session_2")
        self.assertNotEqual(context, context3)

    def test_agent_stats_tracking(self):
        """Test agent statistics tracking"""
        context = self.agent_interface.get_context("stats_agent")

        # Record some operations
        context.record_operation("tool_call", "server1", "tool1", True, 0.5)
        context.record_operation("tool_call", "server1", "tool2", False, 0.3)
        context.record_operation("resource_read", "server1", "uri1", True, 0.2)

        stats = context.get_stats()
        self.assertEqual(stats["tools_called"], 1)
        self.assertEqual(stats["resources_read"], 1)
        self.assertEqual(stats["errors_encountered"], 1)
        self.assertAlmostEqual(stats["avg_tool_latency"], 0.5)

    def test_discovery_with_permissions(self):
        """Test tool and resource discovery with agent permissions"""
        # Create mock server configs with permissions
        from src.mcp_registry import MCPServerConfig

        config1 = MCPServerConfig(
            name="allowed_server",
            transport="stdio",
            allowed_agents=["agent1", "agent2"],
            enabled=True
        )
        config1.tags = ["math", "tools"]

        config2 = MCPServerConfig(
            name="restricted_server",
            transport="stdio",
            allowed_agents=["agent2"],
            enabled=True
        )
        config2.tags = ["files", "tools"]

        self.registry.configs = {
            "allowed_server": config1,
            "restricted_server": config2
        }

        # Mock server status with tools
        from src.mcp_registry import ServerStatus
        from src.mcp_types import MCPTool, MCPResource

        status1 = ServerStatus()
        status1.tools = [
            MCPTool(name="add", description="Add numbers", inputSchema={}),
            MCPTool(name="multiply", description="Multiply numbers", inputSchema={})
        ]
        status1.resources = [
            MCPResource(uri="file://math.txt", name="Math notes", description="Math notes")
        ]

        status2 = ServerStatus()
        status2.tools = [
            MCPTool(name="read_file", description="Read file", inputSchema={})
        ]
        status2.resources = [
            MCPResource(uri="file://data.txt", name="Data file", description="Data file")
        ]

        self.registry.status = {
            "allowed_server": status1,
            "restricted_server": status2
        }

        # Test agent1 access
        tools = self.agent_interface.discover_tools("agent1")
        self.assertEqual(len(tools), 2)  # Can access allowed_server

        resources = self.agent_interface.discover_resources("agent1")
        self.assertEqual(len(resources), 1)  # Can access allowed_server resources

        # Test agent2 access
        tools = self.agent_interface.discover_tools("agent2")
        self.assertEqual(len(tools), 3)  # Can access both servers

        # Test agent3 access (no permissions)
        tools = self.agent_interface.discover_tools("agent3")
        self.assertEqual(len(tools), 0)  # No access


class MCPSecurityIntegrationTest(unittest.TestCase):
    """Test MCP security integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = get_security_manager()

        # Create a mock magic system that doesn't start async tasks
        class MockMagic:
            energy_level = 100
            async def auto_heal(self, *args, **kwargs):
                return False

        self.client = MCPClient("secure_client", magic_system=MockMagic())
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_authenticated_tool_calls(self):
        """Test tool calls with authentication"""
        # Create a test token
        token = await self.security_manager.create_token("test_user", expires_in=3600)
        self.assertIsNotNone(token)
        assert token is not None  # For type checker

        # Authenticate with token
        principal = await self.security_manager.authenticate(token)
        self.assertIsNotNone(principal)
        assert principal is not None  # For type checker
        self.assertEqual(principal.id, "test_user")

        # Test authorization
        authorized = await self.security_manager.authorize(
            principal, "call_tool", "tool:echo"
        )
        self.assertTrue(authorized)

    async def test_rate_limiting_integration(self):
        """Test rate limiting integration"""
        # Create token for rate limiting test
        token = await self.security_manager.create_token("rate_test_user", expires_in=3600)
        self.assertIsNotNone(token)
        assert token is not None  # For type checker

        principal = await self.security_manager.authenticate(token)
        self.assertIsNotNone(principal)
        assert principal is not None  # For type checker

        # Test multiple requests (within limit)
        for i in range(3):
            allowed, reason = await self.security_manager.check_rate_limit(principal, "call_tool")
            self.assertTrue(allowed, f"Request {i+1} should be allowed")

    def test_security_validation(self):
        """Test security validation functions"""
        from src.mcp_security import validate_path_traversal, validate_sql_injection, validate_tool_arguments

        # Test path traversal validation
        self.assertTrue(validate_path_traversal("safe/path/file.txt"))
        self.assertFalse(validate_path_traversal("../../../etc/passwd"))

        # Test SQL injection validation
        self.assertTrue(validate_sql_injection("SELECT * FROM users"))
        self.assertFalse(validate_sql_injection("SELECT * FROM users; DROP TABLE users;"))

        # Test tool argument validation
        safe_args = validate_tool_arguments("read_file", {"path": "safe/file.txt"})
        self.assertEqual(safe_args["path"], "safe/file.txt")

        with self.assertRaises(ValueError):
            validate_tool_arguments("read_file", {"path": "../../../unsafe.txt"})


class MCPConcurrencyIntegrationTest(unittest.TestCase):
    """Test MCP concurrency and performance"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock magic system that doesn't start async tasks
        class MockMagic:
            energy_level = 100
            async def auto_heal(self, *args, **kwargs):
                return False

        self.registry = MCPServerRegistry(magic_system=MockMagic())
        self.agent_interface = MCPAgentInterface(self.registry)

    async def test_concurrent_agent_operations(self):
        """Test concurrent operations from multiple agents"""
        async def agent_task(agent_id: int):
            """Simulate agent operations"""
            context = self.agent_interface.get_context(f"agent_{agent_id}")

            # Record some mock operations
            context.record_operation("tool_call", "mock_server", f"tool_{agent_id}", True, 0.1)
            await asyncio.sleep(0.01)  # Simulate async work
            context.record_operation("resource_read", "mock_server", f"resource_{agent_id}", True, 0.05)

            return context.get_stats()

        # Run multiple agents concurrently
        tasks = [agent_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all agents completed
        self.assertEqual(len(results), 5)
        for stats in results:
            self.assertEqual(stats["tools_called"], 1)
            self.assertEqual(stats["resources_read"], 1)

    def test_performance_metrics(self):
        """Test performance metrics collection"""
        context = self.agent_interface.get_context("perf_agent")

        # Simulate various operations
        operations = [
            ("tool_call", "server1", "tool1", True, 0.1),
            ("tool_call", "server1", "tool2", True, 0.2),
            ("tool_call", "server1", "tool3", False, 0.15),
            ("resource_read", "server1", "res1", True, 0.05),
            ("resource_read", "server1", "res2", True, 0.08),
        ]

        for op_type, server, target, success, latency in operations:
            context.record_operation(op_type, server, target, success, latency)

        stats = context.get_stats()

        self.assertEqual(stats["tools_called"], 2)
        self.assertEqual(stats["resources_read"], 2)
        self.assertEqual(stats["errors_encountered"], 1)
        self.assertAlmostEqual(stats["avg_tool_latency"], 0.15, places=2)
        self.assertAlmostEqual(stats["success_rate"], 0.8, places=1)


def run_integration_tests():
    """Run all MCP integration tests"""
    print("[TEST] Running MCP Integration Test Suite")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        MCPMockServerTest,
        MCPRegistryIntegrationTest,
        MCPAgentIntegrationTest,
        MCPSecurityIntegrationTest,
        MCPConcurrencyIntegrationTest
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY] Test Results:")
    print(f"   Ran: {result.testsRun} tests")
    print(f"   Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Failed: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n[FAILED] Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"   - {test}")

    if result.errors:
        print(f"\n[ERROR] Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"   - {test}")

    if result.wasSuccessful():
        print("\n[SUCCESS] All MCP integration tests passed!")
        return True
    else:
        print("\n[FAILED] Some MCP integration tests failed!")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)