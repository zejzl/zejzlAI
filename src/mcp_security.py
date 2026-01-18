"""
MCP Security Layer for ZEJZL.NET
Implements comprehensive security for MCP protocol including authorization,
rate limiting, audit logging, and access control.
"""

import asyncio
import logging
import time
import hashlib
import secrets
import re
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
import os
from pathlib import Path

logger = logging.getLogger("MCPSecurity")


class SecurityLevel(Enum):
    """Security levels for MCP operations"""
    PUBLIC = "public"        # No authentication required
    USER = "user"           # Basic user authentication
    ADMIN = "admin"         # Administrative access
    SYSTEM = "system"       # System-level access only


class Permission(Enum):
    """Specific permissions for MCP operations"""
    READ_TOOLS = "read_tools"
    CALL_TOOLS = "call_tools"
    READ_RESOURCES = "read_resources"
    WRITE_RESOURCES = "write_resources"
    MANAGE_SERVERS = "manage_servers"
    VIEW_LOGS = "view_logs"
    ADMIN_ACCESS = "admin_access"


@dataclass
class SecurityPrincipal:
    """Security principal (user/agent/system)"""
    id: str
    name: str
    type: str  # "user", "agent", "system"
    security_level: SecurityLevel
    permissions: Set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: Permission) -> bool:
        """Check if principal has specific permission"""
        return permission in self.permissions or self.security_level == SecurityLevel.SYSTEM

    def can_access_level(self, required_level: SecurityLevel) -> bool:
        """Check if principal can access required security level"""
        levels = [SecurityLevel.PUBLIC, SecurityLevel.USER, SecurityLevel.ADMIN, SecurityLevel.SYSTEM]
        principal_idx = levels.index(self.security_level)
        required_idx = levels.index(required_level)
        return principal_idx >= required_idx


@dataclass
class AccessToken:
    """Access token for MCP authentication"""
    token: str
    principal_id: str
    expires_at: datetime
    permissions: Set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now() > self.expires_at

    def has_permission(self, permission: Permission) -> bool:
        """Check if token has specific permission"""
        return permission in self.permissions


@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    name: str
    max_requests: int
    window_seconds: int
    burst_limit: Optional[int] = None
    cooldown_seconds: int = 60

    def get_key(self, identifier: str) -> str:
        """Get rate limit key for identifier"""
        return f"ratelimit:{self.name}:{identifier}"


@dataclass
class AuditEvent:
    """Audit log event"""
    timestamp: datetime
    principal_id: str
    action: str
    resource: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "principal_id": self.principal_id,
            "action": self.action,
            "resource": self.resource,
            "success": self.success,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }


@dataclass
class SecurityMetrics:
    """Security metrics and statistics"""
    total_requests: int = 0
    blocked_requests: int = 0
    rate_limited_requests: int = 0
    auth_failures: int = 0
    audit_events: int = 0
    active_tokens: int = 0
    active_principals: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "auth_failures": self.auth_failures,
            "audit_events": self.audit_events,
            "active_tokens": self.active_tokens,
            "active_principals": self.active_principals,
            "block_rate": self.blocked_requests / max(self.total_requests, 1),
            "auth_failure_rate": self.auth_failures / max(self.total_requests, 1)
        }


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self):
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.cleanup_interval = 300  # 5 minutes
        self._cleanup_started = False

    async def check_limit(self, rule: RateLimitRule, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limit

        Returns:
            Tuple of (allowed: bool, remaining_requests: int)
        """
        # Start cleanup task on first use
        if not self._cleanup_started:
            self._cleanup_started = True
            asyncio.create_task(self._cleanup_task())
        key = rule.get_key(identifier)
        now = time.time()

        if key not in self.buckets:
            # Initialize bucket
            self.buckets[key] = {
                "tokens": rule.max_requests,
                "last_refill": now,
                "burst_tokens": rule.burst_limit or rule.max_requests
            }

        bucket = self.buckets[key]

        # Refill tokens based on time passed
        time_passed = now - bucket["last_refill"]
        refill_amount = int(time_passed * (rule.max_requests / rule.window_seconds))
        bucket["tokens"] = min(rule.max_requests, bucket["tokens"] + refill_amount)
        bucket["last_refill"] = now

        # Check burst limit
        if rule.burst_limit and bucket["burst_tokens"] <= 0:
            return False, 0

        # Check if we have tokens
        if bucket["tokens"] <= 0:
            return False, 0

        # Consume token
        bucket["tokens"] -= 1
        if rule.burst_limit:
            bucket["burst_tokens"] -= 1

        return True, bucket["tokens"]

    async def _cleanup_task(self):
        """Periodic cleanup of old buckets"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            try:
                now = time.time()
                expired_keys = [
                    key for key, bucket in self.buckets.items()
                    if now - bucket["last_refill"] > 3600  # Remove after 1 hour of inactivity
                ]
                for key in expired_keys:
                    del self.buckets[key]
                logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit buckets")
            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")


class MCPSecurityManager:
    """
    Comprehensive security manager for MCP protocol
    Handles authentication, authorization, rate limiting, and audit logging
    """

    def __init__(self, audit_log_path: Optional[str] = None):
        self.principals: Dict[str, SecurityPrincipal] = {}
        self.tokens: Dict[str, AccessToken] = {}
        self.rate_limiter = RateLimiter()
        self.audit_log_path = audit_log_path or "logs/mcp_audit.log"
        self.audit_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = SecurityMetrics()
        self._audit_task_started = False

        # Default rate limit rules
        self.rate_rules = {
            "tool_calls": RateLimitRule("tool_calls", 100, 60, burst_limit=150),  # 100/min, burst 150
            "resource_access": RateLimitRule("resource_access", 200, 60, burst_limit=300),  # 200/min, burst 300
            "server_management": RateLimitRule("server_management", 10, 60),  # 10/min
        }

        # Ensure audit log directory exists
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

        # Create default system principal (don't start async task yet)
        self._create_default_principals()

    def _create_default_principals(self):
        """Create default security principals"""
        # System principal with full access
        system_principal = SecurityPrincipal(
            id="system",
            name="ZEJZL.NET System",
            type="system",
            security_level=SecurityLevel.SYSTEM,
            permissions=set(Permission)
        )
        self.principals["system"] = system_principal

        # Default agent principal
        agent_principal = SecurityPrincipal(
            id="default_agent",
            name="Default Agent",
            type="agent",
            security_level=SecurityLevel.USER,
            permissions={
                Permission.READ_TOOLS,
                Permission.CALL_TOOLS,
                Permission.READ_RESOURCES
            }
        )
        self.principals["default_agent"] = agent_principal

    async def authenticate(self, token: str) -> Optional[SecurityPrincipal]:
        """
        Authenticate using access token

        Args:
            token: Access token string

        Returns:
            SecurityPrincipal if valid, None if invalid/expired
        """
        if token not in self.tokens:
            self.metrics.auth_failures += 1
            await self._audit_event("authentication", "token", False, {"reason": "invalid_token"})
            return None

        access_token = self.tokens[token]
        if access_token.is_expired():
            del self.tokens[token]
            self.metrics.auth_failures += 1
            await self._audit_event("authentication", "token", False, {"reason": "expired_token"})
            return None

        principal = self.principals.get(access_token.principal_id)
        if not principal:
            self.metrics.auth_failures += 1
            await self._audit_event("authentication", "token", False, {"reason": "principal_not_found"})
            return None

        # Update last active
        principal.last_active = datetime.now()

        await self._audit_event("authentication", "token", True, {"principal": principal.id})
        return principal

    async def authorize(self, principal: SecurityPrincipal, action: str, resource: str,
                       required_level: SecurityLevel = SecurityLevel.USER) -> bool:
        """
        Authorize action on resource

        Args:
            principal: Security principal
            action: Action being performed
            resource: Resource being accessed
            required_level: Minimum security level required

        Returns:
            True if authorized, False otherwise
        """
        # Check security level
        if not principal.can_access_level(required_level):
            await self._audit_event(action, resource, False,
                                  {"reason": "insufficient_security_level",
                                   "required": required_level.value,
                                   "actual": principal.security_level.value})
            return False

        # Check specific permissions based on action
        permission_required = self._get_permission_for_action(action)
        if permission_required and not principal.has_permission(permission_required):
            await self._audit_event(action, resource, False,
                                  {"reason": "missing_permission",
                                   "required_permission": permission_required.value})
            return False

        await self._audit_event(action, resource, True, {"principal": principal.id})
        return True

    async def check_rate_limit(self, principal: SecurityPrincipal, action: str) -> Tuple[bool, str]:
        """
        Check rate limits for action

        Args:
            principal: Security principal
            action: Action being performed

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Get appropriate rate limit rule
        rule_name = self._get_rate_rule_for_action(action)
        rule = self.rate_rules.get(rule_name)

        if not rule:
            return True, "no_rate_limit"

        # Check rate limit
        allowed, remaining = await self.rate_limiter.check_limit(rule, principal.id)

        if not allowed:
            self.metrics.rate_limited_requests += 1
            await self._audit_event(action, f"ratelimit:{rule_name}", False,
                                  {"rule": rule_name, "remaining": remaining})
            return False, f"rate_limited:{remaining}"

        return True, f"allowed:{remaining}"

    def _get_permission_for_action(self, action: str) -> Optional[Permission]:
        """Get required permission for action"""
        action_permissions = {
            "call_tool": Permission.CALL_TOOLS,
            "read_tools": Permission.READ_TOOLS,
            "read_resource": Permission.READ_RESOURCES,
            "write_resource": Permission.WRITE_RESOURCES,
            "manage_servers": Permission.MANAGE_SERVERS,
            "view_logs": Permission.VIEW_LOGS,
            "admin": Permission.ADMIN_ACCESS
        }
        return action_permissions.get(action.split("_")[0])

    def _get_rate_rule_for_action(self, action: str) -> str:
        """Get rate limit rule name for action"""
        action_rules = {
            "call_tool": "tool_calls",
            "read_resource": "resource_access",
            "write_resource": "resource_access",
            "manage_servers": "server_management"
        }
        return action_rules.get(action, "tool_calls")

    async def create_token(self, principal_id: str, expires_in: int = 3600,
                          permissions: Optional[Set[Permission]] = None) -> Optional[str]:
        """
        Create access token for principal

        Args:
            principal_id: Principal ID
            expires_in: Token expiration time in seconds
            permissions: Specific permissions for token

        Returns:
            Access token string or None if principal not found
        """
        principal = self.principals.get(principal_id)
        if not principal:
            return None

        token_string = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        token = AccessToken(
            token=token_string,
            principal_id=principal_id,
            expires_at=expires_at,
            permissions=permissions or principal.permissions.copy()
        )

        self.tokens[token_string] = token
        self.metrics.active_tokens = len(self.tokens)

        await self._audit_event("create_token", f"token:{token_string[:8]}", True,
                              {"principal": principal_id, "expires_in": expires_in})

        return token_string

    async def revoke_token(self, token: str) -> bool:
        """Revoke access token"""
        if token in self.tokens:
            del self.tokens[token]
            self.metrics.active_tokens = len(self.tokens)
            await self._audit_event("revoke_token", f"token:{token[:8]}", True)
            return True
        return False

    async def create_principal(self, principal_id: str, name: str, principal_type: str,
                              security_level: SecurityLevel,
                              permissions: Optional[Set[Permission]] = None) -> SecurityPrincipal:
        """Create new security principal"""
        principal = SecurityPrincipal(
            id=principal_id,
            name=name,
            type=principal_type,
            security_level=security_level,
            permissions=permissions or set()
        )

        self.principals[principal_id] = principal
        self.metrics.active_principals = len(self.principals)

        await self._audit_event("create_principal", f"principal:{principal_id}", True,
                              {"type": principal_type, "level": security_level.value})

        return principal

    async def _audit_event(self, action: str, resource: str, success: bool,
                           details: Optional[Dict[str, Any]] = None):
        """Log audit event"""
        # Start audit logging task on first use
        if not self._audit_task_started:
            self._audit_task_started = True
            asyncio.create_task(self._audit_logging_task())

        event = AuditEvent(
            timestamp=datetime.now(),
            principal_id=getattr(asyncio.current_task(), 'principal_id', 'system') if asyncio.current_task() else 'system',
            action=action,
            resource=resource,
            success=success,
            details=details or {}
        )

        await self.audit_queue.put(event)
        self.metrics.audit_events += 1

    async def _audit_logging_task(self):
        """Background task to write audit events to log file"""
        while True:
            try:
                event = await self.audit_queue.get()
                await self._write_audit_event(event)
                self.audit_queue.task_done()
            except Exception as e:
                logger.error(f"Error writing audit event: {e}")
                await asyncio.sleep(1)

    async def _write_audit_event(self, event: AuditEvent):
        """Write audit event to log file"""
        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit event to file: {e}")

    async def get_audit_events(self, limit: int = 100,
                              principal_id: Optional[str] = None,
                              action: Optional[str] = None) -> List[AuditEvent]:
        """Retrieve audit events with optional filtering"""
        events = []
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event_dict = json.loads(line.strip())
                        event = AuditEvent(
                            timestamp=datetime.fromisoformat(event_dict['timestamp']),
                            principal_id=event_dict['principal_id'],
                            action=event_dict['action'],
                            resource=event_dict['resource'],
                            success=event_dict['success'],
                            details=event_dict.get('details', {}),
                            ip_address=event_dict.get('ip_address'),
                            user_agent=event_dict.get('user_agent')
                        )

                        # Apply filters
                        if principal_id and event.principal_id != principal_id:
                            continue
                        if action and event.action != action:
                            continue

                        events.append(event)
                        if len(events) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue

            return events[::-1]  # Return most recent first
        except FileNotFoundError:
            return []

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        return {
            "metrics": self.metrics.to_dict(),
            "active_principals": len(self.principals),
            "active_tokens": len(self.tokens),
            "rate_limit_rules": len(self.rate_rules),
            "audit_log_path": self.audit_log_path
        }

    async def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        expired_tokens = [token for token, access_token in self.tokens.items() if access_token.is_expired()]
        for token in expired_tokens:
            del self.tokens[token]

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
            self.metrics.active_tokens = len(self.tokens)


# Global security manager instance
security_manager = MCPSecurityManager()

# Convenience functions
def get_security_manager() -> MCPSecurityManager:
    """Get the global security manager instance"""
    return security_manager

async def authenticate_token(token: str) -> Optional[SecurityPrincipal]:
    """Convenience function for token authentication"""
    return await security_manager.authenticate(token)

async def check_authorization(principal: SecurityPrincipal, action: str, resource: str,
                            required_level: SecurityLevel = SecurityLevel.USER) -> bool:
    """Convenience function for authorization checking"""
    return await security_manager.authorize(principal, action, resource, required_level)

async def check_rate_limit(principal: SecurityPrincipal, action: str) -> Tuple[bool, str]:
    """Convenience function for rate limit checking"""
    return await security_manager.check_rate_limit(principal, action)


# Input validation and security utilities
def validate_path_traversal(path: str, base_path: Optional[str] = None) -> bool:
    """
    Validate path for traversal attacks.

    Args:
        path: Path to validate
        base_path: Optional base path to resolve against

    Returns:
        True if path is safe, False if traversal detected
    """
    try:
        # Normalize path separators for cross-platform compatibility
        normalized_path = os.path.normpath(path)

        # Check for obvious traversal patterns in normalized path
        if ".." in normalized_path:
            # Count directory traversals
            parts = normalized_path.replace("\\", "/").split("/")
            traversal_count = 0
            safe_parts: List[str] = []

            for part in parts:
                if part == "..":
                    traversal_count += 1
                    if safe_parts:
                        safe_parts.pop()  # Remove parent directory
                    else:
                        # Trying to go above root
                        return False
                elif part not in ("", "."):
                    safe_parts.append(part)

            # If we have more traversals than safe directories, it's suspicious
            if traversal_count > len(safe_parts):
                return False

        # Check for absolute paths that might be dangerous
        if os.path.isabs(path):
            # For now, allow absolute paths but log warning
            # In production, you might want to restrict to allowed directories
            pass

        # If base_path provided, ensure resolved path is within base
        if base_path:
            try:
                base_resolved = Path(base_path).resolve()
                resolved = Path(path).resolve()
                resolved.relative_to(base_resolved)
            except ValueError:
                # Path is outside base directory
                return False

        return True
    except Exception:
        # If path resolution fails, assume it's unsafe
        return False


def validate_sql_injection(query: str) -> bool:
    """
    Basic SQL injection detection for common patterns.

    Args:
        query: SQL query string to validate

    Returns:
        True if query appears safe, False if injection patterns detected
    """
    # Common SQL injection patterns (basic detection)
    dangerous_patterns = [
        r';\s*--',  # Semicolon followed by comment
        r';\s*/\*',  # Semicolon followed by block comment
        r'union\s+select',  # UNION SELECT
        r'/\*.*\*/',  # Block comments that might hide malicious code
        r';\s*drop\s+',  # DROP statements
        r';\s*delete\s+from',  # DELETE statements
        r';\s*update\s+',  # UPDATE statements
        r';\s*insert\s+into',  # INSERT statements
        r';\s*exec\s+',  # EXEC statements
        r';\s*execute\s+',  # EXECUTE statements
        r'--\s*drop',  # Comments hiding DROP
        r'--\s*delete',  # Comments hiding DELETE
    ]

    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return False

    return True


def sanitize_resource_uri(uri: str) -> str:
    """
    Sanitize resource URI to prevent malicious access.

    Args:
        uri: Resource URI to sanitize

    Returns:
        Sanitized URI
    """
    # Basic URI validation - ensure it doesn't contain dangerous schemes or paths
    if "://" in uri:
        # Has scheme, validate it's safe
        scheme = uri.split("://")[0].lower()
        safe_schemes = ["file", "http", "https", "ftp", "ftps"]
        if scheme not in safe_schemes:
            raise ValueError(f"Unsafe URI scheme: {scheme}")

    # Remove any null bytes or other dangerous characters
    sanitized = uri.replace('\x00', '').replace('\r', '').replace('\n', '')

    return sanitized


def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize tool arguments based on tool type.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments

    Returns:
        Validated and sanitized arguments

    Raises:
        ValueError: If arguments are unsafe or invalid
    """
    sanitized_args = {}

    for key, value in arguments.items():
        if isinstance(value, str):
            # For file system tools, validate paths
            if tool_name in ["read_file", "write_file", "list_dir", "delete_file", "move_file"] and key in ["path", "src", "dst"]:
                if not validate_path_traversal(value):
                    raise ValueError(f"Path traversal detected in {key}: {value}")

            # For database tools, check SQL injection
            elif tool_name in ["execute_query", "execute_sql"] and key in ["query", "sql"]:
                if not validate_sql_injection(value):
                    raise ValueError(f"Potential SQL injection detected in {key}")

            # For resource URIs
            elif key == "uri":
                value = sanitize_resource_uri(value)

            # Remove dangerous characters from strings
            sanitized_args[key] = value.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
        else:
            sanitized_args[key] = value

    return sanitized_args


logger.info("MCP Security Layer initialized with comprehensive authorization, rate limiting, and audit logging")