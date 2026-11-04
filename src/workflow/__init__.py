# Ported from grokputer src/workflow/ at d7a14b8 (2026-11-04). Both repos keep their own copy.
"""
Workflow engine for zejzlAI.

DAG execution with parallel batches, a YAML/JSON loader, SQLite state snapshots and
self-healing retries. Ported from grokputer's GG Workflow Framework; the Slack, Notion
and Asana nodes and the RL learning module were left out (see docs/ports/workflow-engine.md).
AgentNode, ORAMNode and the message-bus adapter (node type `bus`) are zejzlAI's own.
"""

from .engine import WorkflowEngine
from .flow import Workflow
from .healing import HealingAction, HealingStrategy, WorkflowHealer, with_healing
from .messagebus_adapter import (
    MessageBusAdapter,
    MessageBusNode,
    get_default_bus,
    get_message_bus_adapter,
    start_default_agents,
    stop_agents,
)
from .loader import NODE_TYPES, WorkflowDefinitionError, build_workflow, load_workflow, read_definition
from .nodes import (
    AgentNode,
    BaseNode,
    ConditionalNode,
    EndNode,
    HTTPNode,
    NodeContext,
    NodeStatus,
    NoOpNode,
    ORAMNode,
    StartNode,
    TransformNode,
)
from .state import StateManager, StateSnapshot, get_state_manager

__version__ = "0.1.0"

__all__ = [
    "Workflow",
    "WorkflowEngine",
    "WorkflowDefinitionError",
    "NODE_TYPES",
    "build_workflow",
    "load_workflow",
    "read_definition",
    "BaseNode",
    "NodeContext",
    "NodeStatus",
    "StartNode",
    "EndNode",
    "NoOpNode",
    "HTTPNode",
    "ConditionalNode",
    "TransformNode",
    "AgentNode",
    "ORAMNode",
    "MessageBusAdapter",
    "MessageBusNode",
    "get_default_bus",
    "get_message_bus_adapter",
    "start_default_agents",
    "stop_agents",
    "StateManager",
    "StateSnapshot",
    "get_state_manager",
    "WorkflowHealer",
    "HealingStrategy",
    "HealingAction",
    "with_healing",
]
