"""Stable public Python API for Sulcus (imported as ``sulcus``)."""

from sulcus.loader import (
    AgentPermissions,
    ExternalAgentManifest,
    inspect_external_agent,
    load_external_agent,
)
from sulcus._version import __version__
from sulcus.ipc import (
    ControlMessage,
    ErrorMessage,
    EventMessage,
    HeartbeatMessage,
    IPCMessage,
    IPCProtocolError,
    TaskRequest,
    TaskResponse,
    make_error,
    make_message,
    parse_message,
)
from sulcus.native import (
    NativeCoreUnavailableError,
    NativeCoreImportError,
    RuntimeCapabilities,
    get_runtime_capabilities,
    native_core_available,
    require_native_core,
)
from sulcus.runtime import (
    AgentToolLoop,
    AgentToolLoopCheckpoint,
    AgentToolLoopConfig,
    AgentToolLoopResult,
    PendingToolApproval,
    ToolApprovalDecision,
    ToolPermissionPolicy,
    ToolResourceLimits,
)
from sulcus.tools import ToolRegistry, ToolRuntime
from kernel.process import AgentProcess, ExecutionMode, RestartPolicy, SupervisorStrategy

__all__ = [
    "AgentProcess",
    "AgentToolLoop",
    "AgentToolLoopCheckpoint",
    "AgentToolLoopConfig",
    "AgentToolLoopResult",
    "AgentPermissions",
    "ControlMessage",
    "ErrorMessage",
    "EventMessage",
    "ExecutionMode",
    "ExternalAgentManifest",
    "HeartbeatMessage",
    "IPCMessage",
    "IPCProtocolError",
    "RestartPolicy",
    "SupervisorStrategy",
    "NativeCoreUnavailableError",
    "NativeCoreImportError",
    "RuntimeCapabilities",
    "get_runtime_capabilities",
    "native_core_available",
    "require_native_core",
    "TaskRequest",
    "TaskResponse",
    "PendingToolApproval",
    "ToolApprovalDecision",
    "ToolPermissionPolicy",
    "ToolRegistry",
    "ToolResourceLimits",
    "ToolRuntime",
    "__version__",
    "make_error",
    "make_message",
    "inspect_external_agent",
    "load_external_agent",
    "parse_message",
]
