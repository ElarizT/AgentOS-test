from __future__ import annotations

import subprocess
import sys
import warnings
from pathlib import Path

import sulcus
import sulcus.ipc
import sulcus.llm
import sulcus.loader
import sulcus.native
import sulcus.runtime
import sulcus.tools
from kernel.agent_tool_loop import AgentToolLoop as InternalAgentToolLoop
from kernel.tools import ToolRegistry as InternalToolRegistry


EXPECTED_TOP_LEVEL_API = {
    "AgentPermissions",
    "AgentProcess",
    "AgentToolLoop",
    "AgentToolLoopCheckpoint",
    "AgentToolLoopConfig",
    "AgentToolLoopResult",
    "ControlMessage",
    "ErrorMessage",
    "EventMessage",
    "ExecutionMode",
    "ExternalAgentManifest",
    "HeartbeatMessage",
    "IPCMessage",
    "IPCProtocolError",
    "NativeCoreImportError",
    "NativeCoreUnavailableError",
    "PendingToolApproval",
    "RestartPolicy",
    "RuntimeCapabilities",
    "SupervisorStrategy",
    "TaskRequest",
    "TaskResponse",
    "ToolApprovalDecision",
    "ToolPermissionPolicy",
    "ToolRegistry",
    "ToolResourceLimits",
    "ToolRuntime",
    "__version__",
    "get_runtime_capabilities",
    "inspect_external_agent",
    "load_external_agent",
    "make_error",
    "make_message",
    "native_core_available",
    "parse_message",
    "require_native_core",
}


def test_top_level_api_snapshot_is_intentional() -> None:
    assert set(sulcus.__all__) == EXPECTED_TOP_LEVEL_API
    assert all(isinstance(name, str) and hasattr(sulcus, name) for name in sulcus.__all__)
    assert sulcus.__version__ == "1.0.0rc1"
    assert not hasattr(sulcus, "LLMRuntime")
    assert not hasattr(sulcus, "sulcus_core")


def test_public_submodule_exports_are_explicit_and_resolvable() -> None:
    for module in (sulcus.ipc, sulcus.llm, sulcus.native, sulcus.runtime, sulcus.tools, sulcus.loader):
        assert all(isinstance(name, str) and hasattr(module, name) for name in module.__all__)
        namespace: dict[str, object] = {}
        exec(f"from {module.__name__} import *", namespace)
        assert {name for name in namespace if not name.startswith("__")} == set(module.__all__)


def test_sulcus_submodules_own_workflow_implementations_and_share_runtime_types() -> None:
    import sulcus.checkpoints
    import sulcus.config
    import sulcus.ipc
    import sulcus.llm
    import sulcus.loader
    import sulcus.native
    import sulcus.runtime
    import sulcus.tools

    from kernel.llm import LLMRuntime

    assert sulcus.config.SulcusConfig.__module__ == "sulcus.config"
    assert sulcus.loader.ExternalAgentManifest.__module__ == "sulcus.loader"
    assert sulcus.checkpoints.CheckpointError.__module__ == "sulcus.checkpoints"
    assert sulcus.runtime.AgentToolLoop is InternalAgentToolLoop
    assert sulcus.tools.ToolRegistry is InternalToolRegistry
    assert sulcus.llm.LLMRuntime is LLMRuntime


def test_public_imports_are_quiet_and_internal_imports_remain_compatible() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import sulcus.native as public_native
        import sulcus.runtime as public_runtime
        import sulcus.tools as public_tools

    assert not caught
    assert public_runtime.AgentToolLoop is InternalAgentToolLoop
    assert public_tools.ToolRegistry is InternalToolRegistry
    assert callable(public_native.native_core_available)


def test_public_import_is_lightweight_in_a_fresh_process() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import sulcus; "
            "assert 'main' not in sys.modules; "
            "assert sulcus.__version__ == '1.0.0rc1'; print('ok')",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=True,
    )
    assert completed.stdout.strip() == "ok"


def test_public_api_quickstart_runs_offline() -> None:
    completed = subprocess.run(
        [sys.executable, "examples/public_api_quickstart.py"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=True,
    )
    assert completed.stdout.strip() == "The answer is 42."
