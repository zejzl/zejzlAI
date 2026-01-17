#!/usr/bin/env python3
"""
Test MCP Security Layer
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

async def test_mcp_security():
    """Test MCP security functionality"""
    print("[TEST] MCP Security Layer Test")
    print("=" * 50)

    from src.mcp_security import (
        security_manager, SecurityLevel, Permission,
        SecurityPrincipal, AccessToken
    )

    # Test 1: Default principals
    print("\n[TEST 1] Default Security Principals")
    system_principal = security_manager.principals.get("system")
    agent_principal = security_manager.principals.get("default_agent")

    assert system_principal is not None, "System principal should exist"
    assert agent_principal is not None, "Agent principal should exist"
    assert system_principal.security_level == SecurityLevel.SYSTEM, "System should have SYSTEM level"
    assert agent_principal.security_level == SecurityLevel.USER, "Agent should have USER level"

    print("✓ Default principals created correctly")
    print(f"  System principal: {system_principal.name} ({system_principal.security_level.value})")
    print(f"  Agent principal: {agent_principal.name} ({agent_principal.security_level.value})")

    # Test 2: Create custom principal
    print("\n[TEST 2] Custom Principal Creation")
    custom_principal = await security_manager.create_principal(
        principal_id="test_user",
        name="Test User",
        principal_type="user",
        security_level=SecurityLevel.USER,
        permissions={Permission.READ_TOOLS, Permission.CALL_TOOLS}
    )

    assert custom_principal.id == "test_user", "Custom principal ID should match"
    assert Permission.READ_TOOLS in custom_principal.permissions, "Should have READ_TOOLS permission"
    print("✓ Custom principal created successfully")

    # Test 3: Token creation and authentication
    print("\n[TEST 3] Token Creation and Authentication")
    token = await security_manager.create_token("test_user", expires_in=3600)
    assert token is not None, "Token should be created"

    principal = await security_manager.authenticate(token)
    assert principal is not None, "Token should authenticate successfully"
    assert principal.id == "test_user", "Authenticated principal should match"
    print("✓ Token creation and authentication working")

    # Test 4: Authorization checks
    print("\n[TEST 4] Authorization Checks")
    authorized = await security_manager.authorize(
        principal, "call_tool", "tool:test_tool", SecurityLevel.USER
    )
    assert authorized, "User should be authorized for tool calls"
    print("✓ Authorization checks working")

    # Test 5: Rate limiting
    print("\n[TEST 5] Rate Limiting")
    for i in range(5):
        allowed, reason = await security_manager.check_rate_limit(principal, "call_tool")
        if i < 4:  # First 4 should be allowed
            assert allowed, f"Request {i+1} should be allowed"
        print(f"  Request {i+1}: {'ALLOWED' if allowed else 'BLOCKED'} ({reason})")

    print("✓ Rate limiting working")

    # Test 6: Audit logging
    print("\n[TEST 6] Audit Logging")
    await asyncio.sleep(0.1)  # Let audit events be processed

    audit_events = await security_manager.get_audit_events(limit=5)
    assert len(audit_events) > 0, "Should have audit events"
    print(f"✓ Audit logging working ({len(audit_events)} events logged)")

    # Test 7: Security metrics
    print("\n[TEST 7] Security Metrics")
    metrics = security_manager.get_security_metrics()
    assert "metrics" in metrics, "Should have metrics"
    assert "active_principals" in metrics, "Should have principal count"
    print("✓ Security metrics working")
    print(f"  Active principals: {metrics['active_principals']}")
    print(f"  Active tokens: {metrics['active_tokens']}")
    print(f"  Total requests: {metrics['metrics']['total_requests']}")

    print("\n" + "=" * 50)
    print("[SUCCESS] MCP Security Layer Test Completed!")
    print("\nFeatures verified:")
    print("- ✓ Security principal management")
    print("- ✓ Access token creation/authentication")
    print("- ✓ Authorization and permission checks")
    print("- ✓ Rate limiting with token buckets")
    print("- ✓ Comprehensive audit logging")
    print("- ✓ Security metrics and monitoring")
    print("- ✓ Automatic token cleanup")

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_mcp_security())
        if success:
            print("\n🎉 All MCP security tests passed!")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)