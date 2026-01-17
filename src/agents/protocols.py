# src/agents/protocols.py
"""
Inter-Agent Communication Protocols for ZEJZL.NET Pantheon System.

Standardized messaging formats and protocols for agent-to-agent communication,
enabling coordinated multi-agent operations with clear message semantics.
"""

import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum


class MessageType(Enum):
    """Types of inter-agent messages"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    COORDINATION = "coordination"
    DATA_SHARE = "data_share"
    VALIDATION_REQUEST = "validation_request"
    VALIDATION_RESPONSE = "validation_response"
    EXECUTION_REQUEST = "execution_request"
    EXECUTION_RESPONSE = "execution_response"


class AgentRole(Enum):
    """Agent roles in the Pantheon system"""
    OBSERVER = "observer"
    REASONER = "reasoner"
    ACTOR = "actor"
    VALIDATOR = "validator"
    EXECUTOR = "executor"
    ANALYZER = "analyzer"
    LEARNER = "learner"
    IMPROVER = "improver"
    MEMORY = "memory"


@dataclass
class AgentMessage:
    """Base class for all inter-agent messages"""
    message_id: str
    message_type: MessageType
    sender_role: AgentRole
    receiver_role: Optional[AgentRole]
    timestamp: datetime
    conversation_id: str
    payload: Dict[str, Any]
    priority: int = 1  # 1=low, 5=high
    requires_response: bool = False
    correlation_id: Optional[str] = None  # For request-response pairs

    @classmethod
    def create(cls, message_type: MessageType, sender_role: AgentRole,
               receiver_role: Optional[AgentRole], payload: Dict[str, Any],
               conversation_id: str = "default", priority: int = 1,
               requires_response: bool = False, correlation_id: Optional[str] = None):
        """Factory method to create a new agent message"""
        return cls(
            message_id=str(uuid4()),
            message_type=message_type,
            sender_role=sender_role,
            receiver_role=receiver_role,
            timestamp=datetime.now(),
            conversation_id=conversation_id,
            payload=payload,
            priority=priority,
            requires_response=requires_response,
            correlation_id=correlation_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['sender_role'] = self.sender_role.value
        if self.receiver_role:
            data['receiver_role'] = self.receiver_role.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        data_copy = data.copy()
        data_copy['message_type'] = MessageType(data['message_type'])
        data_copy['sender_role'] = AgentRole(data['sender_role'])
        if 'receiver_role' in data and data['receiver_role']:
            data_copy['receiver_role'] = AgentRole(data['receiver_role'])
        return cls(**data_copy)


@dataclass
class TaskRequest(AgentMessage):
    """Request for task execution"""
    task_description: str = ""
    required_specialization: Optional[str] = None
    deadline: Optional[datetime] = None
    dependencies: Optional[List[str]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class TaskResponse(AgentMessage):
    """Response to task request"""
    success: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class StatusUpdate(AgentMessage):
    """Agent status update"""
    status: str = "idle"  # "idle", "busy", "error", "maintenance"
    current_task: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0
    health_score: float = 1.0  # 0.0 to 1.0


@dataclass
class CoordinationMessage(AgentMessage):
    """Coordination message between agents"""
    coordination_type: str = "sync"  # "sync", "delegate", "escalate", "collaborate"
    target_agents: Optional[List[AgentRole]] = None
    coordination_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.target_agents is None:
            self.target_agents = []
        if self.coordination_data is None:
            self.coordination_data = {}


@dataclass
class DataShareMessage(AgentMessage):
    """Data sharing between agents"""
    data_type: str = "observation"  # "observation", "analysis", "pattern", "metric"
    data: Optional[Dict[str, Any]] = None
    sharing_reason: str = ""

    def __post_init__(self):
        if self.data is None:
            self.data = {}


@dataclass
class ValidationRequest(AgentMessage):
    """Request for validation"""
    item_to_validate: Optional[Dict[str, Any]] = None
    validation_criteria: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.item_to_validate is None:
            self.item_to_validate = {}
        if self.validation_criteria is None:
            self.validation_criteria = {}


@dataclass
class ValidationResponse(AgentMessage):
    """Response to validation request"""
    is_valid: bool = False
    validation_details: Dict[str, Any] = None
    recommendations: Optional[List[str]] = None

    def __post_init__(self):
        if self.validation_details is None:
            self.validation_details = {}
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class ExecutionRequest(AgentMessage):
    """Request for execution"""
    action: str = ""
    parameters: Optional[Dict[str, Any]] = None
    safety_checks: Optional[List[str]] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.safety_checks is None:
            self.safety_checks = []


@dataclass
class ExecutionResponse(AgentMessage):
    """Response to execution request"""
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None
    execution_error: Optional[str] = None
    retry_count: int = 0


class AgentProtocol:
    """
    Protocol handler for standardized agent communication
    """

    def __init__(self):
        self.message_handlers: Dict[MessageType, callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}

    def register_handler(self, message_type: MessageType, handler: callable):
        """Register a handler for a message type"""
        self.message_handlers[message_type] = handler

    async def send_message(self, message: AgentMessage, target_agent: Optional['AgentProtocol'] = None) -> Optional[AgentMessage]:
        """
        Send a message to target agent and optionally wait for response
        """
        if target_agent:
            return await target_agent.receive_message(message)
        else:
            # Broadcast or handle locally
            return await self.handle_message(message)

    async def receive_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Receive and process an incoming message"""
        return await self.handle_message(message)

    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle incoming message using registered handlers"""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                response = await handler(message)
                if message.requires_response and response:
                    response.correlation_id = message.message_id
                return response
            except Exception as e:
                # Return error response
                return AgentMessage.create(
                    MessageType.TASK_RESPONSE,
                    message.receiver_role or AgentRole.OBSERVER,
                    message.sender_role,
                    {"error": str(e)},
                    message.conversation_id,
                    correlation_id=message.message_id
                )
        else:
            logger.warning(f"No handler for message type: {message.message_type}")
        return None

    async def wait_for_response(self, message_id: str, timeout: float = 30.0) -> Optional[AgentMessage]:
        """Wait for a response to a sent message"""
        future = self.pending_responses.get(message_id)
        if future:
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                del self.pending_responses[message_id]
        return None


# Import logger for protocol use
import logging
logger = logging.getLogger("AgentProtocol")