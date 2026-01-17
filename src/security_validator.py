"""
Security Validation and Policy Enforcement for ZEJZL.NET
Implements command safety analysis, user approval gates, and risk assessment.
"""

import re
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("SecurityValidator")


class RiskLevel(Enum):
    """Risk levels for operations"""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class ApprovalRequirement(Enum):
    """Approval requirements for operations"""
    NONE = "none"              # No approval needed
    LOG_ONLY = "log_only"      # Log but allow
    USER_CONFIRM = "user_confirm"  # Require user confirmation
    ADMIN_APPROVE = "admin_approve"  # Require admin approval
    BLOCKED = "blocked"        # Operation blocked


@dataclass
class SecurityPolicy:
    """Security policy for operations"""
    name: str
    risk_level: RiskLevel
    approval_required: ApprovalRequirement
    description: str
    patterns: List[str]  # Regex patterns to match
    allowed_users: Optional[Set[str]] = None
    blocked_users: Optional[Set[str]] = None


@dataclass
class ValidationResult:
    """Result of security validation"""
    is_safe: bool
    risk_level: RiskLevel
    approval_required: ApprovalRequirement
    violations: List[str]
    recommendations: List[str]
    requires_user_approval: bool
    requires_admin_approval: bool
    can_proceed: bool


class SecurityValidator:
    """
    Advanced security validation system for ZEJZL.NET operations.
    Analyzes commands, operations, and execution results for safety and compliance.
    """

    def __init__(self):
        self.policies = self._load_default_policies()
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def _load_default_policies(self) -> List[SecurityPolicy]:
        """Load default security policies"""
        return [
            # File system operations
            SecurityPolicy(
                name="safe_read_operations",
                risk_level=RiskLevel.SAFE,
                approval_required=ApprovalRequirement.NONE,
                description="Safe read-only file operations",
                patterns=[
                    r"^ls\s",           # List directory
                    r"^cat\s",          # View file contents
                    r"^head\s",         # View file beginning
                    r"^tail\s",         # View file end
                    r"^find\s.*-name",  # Safe find operations
                    r"^pwd$",           # Print working directory
                    r"^whoami$",        # Current user
                ]
            ),

            SecurityPolicy(
                name="low_risk_file_ops",
                risk_level=RiskLevel.LOW_RISK,
                approval_required=ApprovalRequirement.LOG_ONLY,
                description="Low-risk file operations",
                patterns=[
                    r"^mkdir\s",        # Create directory
                    r"^touch\s",        # Create empty file
                    r"^cp\s.*\.bak$",  # Copy to backup
                    r"^mv\s.*\.bak$",  # Move to backup
                ]
            ),

            SecurityPolicy(
                name="medium_risk_file_ops",
                risk_level=RiskLevel.MEDIUM_RISK,
                approval_required=ApprovalRequirement.USER_CONFIRM,
                description="Medium-risk file operations",
                patterns=[
                    r"^rm\s[^-]*$",    # Remove files (not recursive)
                    r"^mv\s",           # Move/rename files
                    r"^cp\s",           # Copy files
                    r"^chmod\s",        # Change permissions
                    r"^chown\s",        # Change ownership
                ]
            ),

            SecurityPolicy(
                name="high_risk_file_ops",
                risk_level=RiskLevel.HIGH_RISK,
                approval_required=ApprovalRequirement.USER_CONFIRM,
                description="High-risk file operations",
                patterns=[
                    r"^rm\s.*-r",      # Recursive remove
                    r"^rm\s.*-f",      # Force remove
                    r"^rm\s.*/",       # Remove directories
                    r"^rmdir\s",       # Remove directories
                    r"^dd\s",          # Disk operations
                    r"^mkfs",          # Format filesystem
                    r"^fdisk",         # Partition operations
                ]
            ),

            SecurityPolicy(
                name="critical_system_ops",
                risk_level=RiskLevel.CRITICAL,
                approval_required=ApprovalRequirement.ADMIN_APPROVE,
                description="Critical system operations",
                patterns=[
                    r"^rm\s-rf\s/",   # Remove root filesystem
                    r"^rm\s-rf\s/\*", # Remove everything
                    r"^format\s",     # Format commands
                    r"^fdisk\s.*delete", # Delete partitions
                    r"^shutdown",     # System shutdown
                    r"^reboot",       # System reboot
                    r"^halt",         # System halt
                ]
            ),

            # Network operations
            SecurityPolicy(
                name="network_read",
                risk_level=RiskLevel.SAFE,
                approval_required=ApprovalRequirement.NONE,
                description="Safe network read operations",
                patterns=[
                    r"^ping\s",        # Ping hosts
                    r"^nslookup\s",    # DNS lookup
                    r"^dig\s",         # DNS query
                    r"^curl\s.*--head", # HTTP HEAD requests
                ]
            ),

            SecurityPolicy(
                name="network_write",
                risk_level=RiskLevel.MEDIUM_RISK,
                approval_required=ApprovalRequirement.USER_CONFIRM,
                description="Network write operations",
                patterns=[
                    r"^curl\s.*-X\s(POST|PUT|DELETE|PATCH)",
                    r"^wget\s.*--post",
                    r"^ssh\s.*(scp|rsync)",
                ]
            ),

            # Database operations
            SecurityPolicy(
                name="db_read",
                risk_level=RiskLevel.SAFE,
                approval_required=ApprovalRequirement.NONE,
                description="Safe database read operations",
                patterns=[
                    r"SELECT\s.*FROM",
                    r"SHOW\s.*TABLES",
                    r"DESCRIBE\s",
                    r"EXPLAIN\s",
                ]
            ),

            SecurityPolicy(
                name="db_write",
                risk_level=RiskLevel.MEDIUM_RISK,
                approval_required=ApprovalRequirement.USER_CONFIRM,
                description="Database write operations",
                patterns=[
                    r"INSERT\sINTO",
                    r"UPDATE\s",
                    r"DELETE\sFROM",
                    r"DROP\s",
                    r"CREATE\s",
                    r"ALTER\s",
                ]
            ),

            # System operations
            SecurityPolicy(
                name="system_info",
                risk_level=RiskLevel.SAFE,
                approval_required=ApprovalRequirement.NONE,
                description="Safe system information",
                patterns=[
                    r"^ps\s",          # Process list
                    r"^top$",          # System monitor
                    r"^df\s",          # Disk usage
                    r"^free$",         # Memory usage
                    r"^uptime$",       # System uptime
                    r"^uname",         # System info
                ]
            ),

            SecurityPolicy(
                name="system_admin",
                risk_level=RiskLevel.HIGH_RISK,
                approval_required=ApprovalRequirement.ADMIN_APPROVE,
                description="System administration operations",
                patterns=[
                    r"^sudo\s",        # Superuser operations
                    r"^su\s",          # Switch user
                    r"^mount\s",       # Mount filesystems
                    r"^umount\s",      # Unmount filesystems
                    r"^systemctl\s",   # System service control
                    r"^service\s",     # Service management
                ]
            ),

            # Blocked operations
            SecurityPolicy(
                name="blocked_operations",
                risk_level=RiskLevel.CRITICAL,
                approval_required=ApprovalRequirement.BLOCKED,
                description="Blocked dangerous operations",
                patterns=[
                    r"rm\s-rf\s/\*",  # Delete everything
                    r">/dev/sd",      # Write to disk devices
                    r"dd.*of=/dev",  # Disk operations on devices
                    r"mkfs.*/dev",   # Format disk devices
                    r"fdisk.*/dev",  # Partition operations
                    r"wipefs",       # Wipe filesystem signatures
                ]
            )
        ]

    def validate_operation(self, operation: str, context: Optional[Dict[str, Any]] = None,
                          user: Optional[str] = None) -> ValidationResult:
        """
        Validate an operation against security policies.

        Args:
            operation: The operation/command to validate
            context: Additional context about the operation
            user: User performing the operation

        Returns:
            ValidationResult with safety assessment and requirements
        """
        violations = []
        recommendations = []
        matched_policies = []

        # Check against all policies
        for policy in self.policies:
            if self._matches_policy(operation, policy):
                matched_policies.append(policy)

                # Check user restrictions
                if policy.blocked_users and user in policy.blocked_users:
                    violations.append(f"User '{user}' is blocked from this operation")
                elif policy.allowed_users and user not in policy.allowed_users:
                    violations.append(f"User '{user}' is not authorized for this operation")

        if not matched_policies:
            # No matching policy - default to medium risk with user confirmation
            risk_level = RiskLevel.MEDIUM_RISK
            approval_required = ApprovalRequirement.USER_CONFIRM
            recommendations.append("Operation not covered by existing policies - manual review recommended")
        else:
            # Use the highest risk policy that matched
            highest_risk_policy = max(matched_policies, key=lambda p: self._risk_level_value(p.risk_level))
            risk_level = highest_risk_policy.risk_level
            approval_required = highest_risk_policy.approval_required

        # Determine approval requirements
        requires_user_approval = approval_required in [ApprovalRequirement.USER_CONFIRM]
        requires_admin_approval = approval_required in [ApprovalRequirement.ADMIN_APPROVE]
        can_proceed = approval_required not in [ApprovalRequirement.BLOCKED]

        # Add recommendations based on risk level
        if risk_level == RiskLevel.HIGH_RISK:
            recommendations.append("High-risk operation - ensure backups are current")
            recommendations.append("Consider testing in a safe environment first")
        elif risk_level == RiskLevel.CRITICAL:
            recommendations.append("Critical operation - requires senior approval")
            recommendations.append("Document the operation and rationale")

        # Check for dangerous patterns in the operation itself
        dangerous_patterns = [
            (r"rm\s.*\*\*", "Very dangerous wildcard usage"),
            (r"dd.*if=/dev/zero", "Data destruction operation"),
            (r">.*\.bash_history", "History manipulation"),
            (r"chmod\s.*777", "Overly permissive permissions"),
        ]

        for pattern, warning in dangerous_patterns:
            if re.search(pattern, operation, re.IGNORECASE):
                violations.append(f"Pattern detected: {warning}")
                if self._risk_level_value(risk_level) < self._risk_level_value(RiskLevel.HIGH_RISK):
                    risk_level = RiskLevel.HIGH_RISK

        return ValidationResult(
            is_safe=risk_level in [RiskLevel.SAFE, RiskLevel.LOW_RISK] and not violations,
            risk_level=risk_level,
            approval_required=approval_required,
            violations=violations,
            recommendations=recommendations,
            requires_user_approval=requires_user_approval,
            requires_admin_approval=requires_admin_approval,
            can_proceed=can_proceed
        )

    def validate_execution_result(self, execution_result: Dict[str, Any]) -> ValidationResult:
        """
        Validate the results of an execution for safety and quality.

        Args:
            execution_result: The execution result to validate

        Returns:
            ValidationResult with assessment of the execution
        """
        violations = []
        recommendations = []
        risk_level = RiskLevel.SAFE

        # Check for execution errors
        if execution_result.get("status") == "error":
            error_msg = execution_result.get("error", "")
            if "permission denied" in error_msg.lower():
                violations.append("Permission error - operation may require elevated privileges")
                if self._risk_level_value(risk_level) < self._risk_level_value(RiskLevel.MEDIUM_RISK):
                    risk_level = RiskLevel.MEDIUM_RISK
            elif "no such file" in error_msg.lower():
                violations.append("File not found - verify paths are correct")
                risk_level = RiskLevel.LOW_RISK
            else:
                violations.append(f"Execution error: {error_msg}")
                if self._risk_level_value(risk_level) < self._risk_level_value(RiskLevel.MEDIUM_RISK):
                    risk_level = RiskLevel.MEDIUM_RISK

        # Check execution time (very long operations might indicate issues)
        execution_time = execution_result.get("execution_time", 0)
        if execution_time > 300:  # 5 minutes
            recommendations.append(f"Long execution time ({execution_time}s) - monitor for performance issues")
            risk_level = max(risk_level, RiskLevel.LOW_RISK)

        # Check for dangerous output patterns
        output = execution_result.get("output", "")
        dangerous_outputs = [
            ("segmentation fault", "Memory corruption detected"),
            ("killed", "Process was killed - possible resource issue"),
            ("permission denied", "Access permission issues"),
            ("disk full", "Storage capacity issues"),
        ]

        for pattern, issue in dangerous_outputs:
            if pattern in output.lower():
                violations.append(f"Output indicates: {issue}")
                if self._risk_level_value(risk_level) < self._risk_level_value(RiskLevel.MEDIUM_RISK):
                    risk_level = RiskLevel.MEDIUM_RISK

        # Determine approval requirements based on violations
        if violations:
            if risk_level == RiskLevel.CRITICAL:
                approval_required = ApprovalRequirement.ADMIN_APPROVE
            elif risk_level == RiskLevel.HIGH_RISK:
                approval_required = ApprovalRequirement.USER_CONFIRM
            else:
                approval_required = ApprovalRequirement.LOG_ONLY
        else:
            approval_required = ApprovalRequirement.NONE

        return ValidationResult(
            is_safe=not violations and risk_level != RiskLevel.CRITICAL,
            risk_level=risk_level,
            approval_required=approval_required,
            violations=violations,
            recommendations=recommendations,
            requires_user_approval=approval_required == ApprovalRequirement.USER_CONFIRM,
            requires_admin_approval=approval_required == ApprovalRequirement.ADMIN_APPROVE,
            can_proceed=risk_level != RiskLevel.CRITICAL
        )

    def _matches_policy(self, operation: str, policy: SecurityPolicy) -> bool:
        """Check if an operation matches a security policy"""
        for pattern in policy.patterns:
            if re.search(pattern, operation, re.IGNORECASE):
                return True
        return False

    def _risk_level_value(self, risk_level: RiskLevel) -> int:
        """Get numeric value for risk level comparison"""
        values = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW_RISK: 1,
            RiskLevel.MEDIUM_RISK: 2,
            RiskLevel.HIGH_RISK: 3,
            RiskLevel.CRITICAL: 4
        }
        return values.get(risk_level, 0)

    async def request_user_approval(self, operation: str, validation: ValidationResult,
                                   user_id: str) -> bool:
        """
        Request user approval for an operation.

        Args:
            operation: The operation requiring approval
            validation: Validation result
            user_id: User to request approval from

        Returns:
            True if approved, False otherwise
        """
        approval_id = f"approval_{user_id}_{hash(operation)}"

        self.pending_approvals[approval_id] = {
            "operation": operation,
            "validation": validation,
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time(),
            "status": "pending"
        }

        # In a real system, this would send notifications to the user
        # For now, we'll simulate by logging and requiring manual approval
        logger.warning(f"USER APPROVAL REQUIRED for operation: {operation}")
        logger.warning(f"Risk Level: {validation.risk_level.value}")
        logger.warning(f"Violations: {validation.violations}")
        logger.warning(f"Approval ID: {approval_id}")

        # For demo purposes, we'll auto-approve low-risk operations
        if validation.risk_level in [RiskLevel.SAFE, RiskLevel.LOW_RISK]:
            logger.info(f"Auto-approving low-risk operation: {operation}")
            self.pending_approvals[approval_id]["status"] = "approved"
            return True

        # High-risk operations require explicit approval
        return False  # Would wait for user input in real system

    def approve_operation(self, approval_id: str, approved: bool, admin_user: Optional[str] = None) -> bool:
        """
        Approve or deny a pending operation.

        Args:
            approval_id: The approval request ID
            approved: Whether the operation is approved
            admin_user: Admin user approving (for admin approvals)

        Returns:
            True if approval was processed successfully
        """
        if approval_id not in self.pending_approvals:
            logger.error(f"Approval ID not found: {approval_id}")
            return False

        approval = self.pending_approvals[approval_id]
        validation = approval["validation"]

        if validation.requires_admin_approval and not admin_user:
            logger.error(f"Admin approval required for: {approval_id}")
            return False

        approval["status"] = "approved" if approved else "denied"
        approval["approved_by"] = admin_user or approval["user_id"]
        approval["approved_at"] = asyncio.get_event_loop().time()

        logger.info(f"Operation {approval_id} {'approved' if approved else 'denied'} by {approval['approved_by']}")

        return True

    def get_pending_approvals(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending approval requests"""
        pending = [
            approval for approval in self.pending_approvals.values()
            if approval["status"] == "pending" and (not user_id or approval["user_id"] == user_id)
        ]
        return pending

    def get_security_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security report"""
        total_operations = len(self.pending_approvals)
        approved_ops = sum(1 for op in self.pending_approvals.values() if op["status"] == "approved")
        denied_ops = sum(1 for op in self.pending_approvals.values() if op["status"] == "denied")
        pending_ops = sum(1 for op in self.pending_approvals.values() if op["status"] == "pending")

        # Risk distribution
        risk_counts = {}
        for approval in self.pending_approvals.values():
            risk = approval["validation"].risk_level.value
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        return {
            "total_operations": total_operations,
            "approved_operations": approved_ops,
            "denied_operations": denied_ops,
            "pending_operations": pending_ops,
            "risk_distribution": risk_counts,
            "active_policies": len(self.policies),
            "policy_violations": sum(len(op["validation"].violations) for op in self.pending_approvals.values())
        }


# Global security validator instance
security_validator = SecurityValidator()

logger.info("Security Validator initialized with comprehensive command safety analysis and approval gates")