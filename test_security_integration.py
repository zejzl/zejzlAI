#!/usr/bin/env python3
"""
Test script for Security Validator integration with ValidatorAgent
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.security_validator import security_validator, RiskLevel, ApprovalRequirement
from src.agents.validator import ValidatorAgent

async def test_security_validator():
    """Test the security validator with various commands"""
    print("Testing Security Validator...")

    # Test safe commands
    safe_commands = [
        "ls -la",
        "cat /etc/passwd",  # Actually dangerous, but let's see
        "ping google.com",
        "ps aux"
    ]

    # Test dangerous commands
    dangerous_commands = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "rm -rf /*",
        "sudo rm -rf /etc"
    ]

    print("\nTesting SAFE commands:")
    for cmd in safe_commands:
        result = security_validator.validate_operation(cmd)
        print(f"  {cmd}: {result.risk_level.value} - {result.approval_required.value} - Can proceed: {result.can_proceed}")

    print("\nTesting DANGEROUS commands:")
    for cmd in dangerous_commands:
        result = security_validator.validate_operation(cmd)
        print(f"  {cmd}: {result.risk_level.value} - {result.approval_required.value} - Can proceed: {result.can_proceed}")

async def test_validator_agent():
    """Test the updated ValidatorAgent"""
    print("\nTesting ValidatorAgent integration...")

    agent = ValidatorAgent()

    # Test operation validation
    print("\nTesting operation validation:")
    test_operations = [
        "ls -la",           # Safe
        "rm -rf /tmp/*",    # Medium risk
        "rm -rf /",         # Critical
    ]

    for op in test_operations:
        result = await agent.validate_operation(op)
        print(f"  {op}: {result.risk_level.value} - Can proceed: {result.can_proceed}")

    # Test execution validation
    print("\nTesting execution validation:")
    test_executions = [
        {"status": "completed", "output": "Files listed successfully"},
        {"status": "error", "error": "Permission denied", "output": ""},
        {"status": "completed", "execution_time": 350}  # Long execution
    ]

    for execution in test_executions:
        result = await agent.validate_execution_result(execution)
        print(f"  Status: {execution.get('status', 'unknown')} - Risk: {result.risk_level.value} - Can proceed: {result.can_proceed}")

async def main():
    """Main test function"""
    print("ZEJZL.NET Security Validator Integration Test")
    print("=" * 50)

    try:
        await test_security_validator()
        await test_validator_agent()

        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())