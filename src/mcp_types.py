"""
MCP Protocol Types and Schemas for ZEJZL.NET

Implements Model Context Protocol (MCP) type definitions following the official spec.
Provides type-safe data structures for MCP JSON-RPC 2.0 communication.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import json


class MCPErrorCode(Enum):
    """Standard MCP error codes following JSON-RPC 2.0"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific error codes
    RESOURCE_NOT_FOUND = -32001
    TOOL_NOT_FOUND = -32002
    PERMISSION_DENIED = -32003
    TIMEOUT = -32004
    RATE_LIMITED = -32005


class MCPTransport(Enum):
    """MCP transport mechanisms"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


@dataclass
class MCPError:
    """MCP error response"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPError":
        return cls(
            code=data["code"],
            message=data["message"],
            data=data.get("data")
        )


@dataclass
class MCPRequest:
    """MCP JSON-RPC 2.0 request"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.id is not None:
            result["id"] = self.id
        if self.params:
            result["params"] = self.params
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data["method"],
            params=data.get("params")
        )


@dataclass
class MCPResponse:
    """MCP JSON-RPC 2.0 response"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[MCPError] = None

    def to_dict(self) -> Dict[str, Any]:
        result_dict = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error:
            result_dict["error"] = self.error.to_dict()
        else:
            result_dict["result"] = self.result
        return result_dict

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResponse":
        error = None
        if "error" in data:
            error = MCPError.from_dict(data["error"])

        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=error
        )


@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]  # JSON Schema for tool parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPTool":
        return cls(
            name=data["name"],
            description=data["description"],
            inputSchema=data["inputSchema"]
        )


@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "uri": self.uri,
            "name": self.name
        }
        if self.description:
            result["description"] = self.description
        if self.mimeType:
            result["mimeType"] = self.mimeType
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResource":
        return cls(
            uri=data["uri"],
            name=data["name"],
            description=data.get("description"),
            mimeType=data.get("mimeType")
        )


@dataclass
class MCPPrompt:
    """MCP prompt template"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.arguments:
            result["arguments"] = self.arguments
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPPrompt":
        return cls(
            name=data["name"],
            description=data.get("description"),
            arguments=data.get("arguments")
        )


@dataclass
class MCPServerCapabilities:
    """MCP server capability advertisement"""
    tools: Optional[List[MCPTool]] = None
    resources: Optional[List[MCPResource]] = None
    prompts: Optional[List[MCPPrompt]] = None
    experimental: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tools:
            result["tools"] = [t.to_dict() for t in self.tools]
        if self.resources:
            result["resources"] = [r.to_dict() for r in self.resources]
        if self.prompts:
            result["prompts"] = [p.to_dict() for p in self.prompts]
        if self.experimental:
            result["experimental"] = self.experimental
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerCapabilities":
        tools = None
        if "tools" in data:
            tools = [MCPTool.from_dict(t) for t in data["tools"]]

        resources = None
        if "resources" in data:
            resources = [MCPResource.from_dict(r) for r in data["resources"]]

        prompts = None
        if "prompts" in data:
            prompts = [MCPPrompt.from_dict(p) for p in data["prompts"]]

        return cls(
            tools=tools,
            resources=resources,
            prompts=prompts,
            experimental=data.get("experimental")
        )


@dataclass
class MCPServerInfo:
    """MCP server information from initialize response"""
    name: str
    version: str
    capabilities: MCPServerCapabilities
    protocolVersion: str = "2024-11-05"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "protocolVersion": self.protocolVersion,
            "capabilities": self.capabilities.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerInfo":
        return cls(
            name=data["name"],
            version=data["version"],
            protocolVersion=data.get("protocolVersion", "2024-11-05"),
            capabilities=MCPServerCapabilities.from_dict(data["capabilities"])
        )


@dataclass
class MCPClientInfo:
    """MCP client information for initialize request"""
    name: str = "ZEJZL.NET"
    version: str = "0.0.8"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version
        }


# MCP Method Names (Standard Protocol)
class MCPMethod:
    """Standard MCP protocol methods"""
    # Lifecycle
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    SHUTDOWN = "shutdown"

    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"

    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"

    # Sampling (AI model sampling)
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"


# Validation helpers
def validate_json_rpc_request(data: Dict[str, Any]) -> bool:
    """Validate JSON-RPC 2.0 request structure"""
    if not isinstance(data, dict):
        return False

    if data.get("jsonrpc") != "2.0":
        return False

    if "method" not in data:
        return False

    if not isinstance(data["method"], str):
        return False

    return True


def validate_json_rpc_response(data: Dict[str, Any]) -> bool:
    """Validate JSON-RPC 2.0 response structure"""
    if not isinstance(data, dict):
        return False

    if data.get("jsonrpc") != "2.0":
        return False

    if "id" not in data:
        return False

    # Must have either result or error, not both
    has_result = "result" in data
    has_error = "error" in data

    if has_result and has_error:
        return False

    if not has_result and not has_error:
        return False

    return True
