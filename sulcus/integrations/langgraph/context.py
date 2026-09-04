"""Execution and checkpoint context views for LangGraph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ExecutionContext:
    """Sulcus view of one LangGraph execution.

    State is deliberately kept out of runtime-event metadata.  Consumers that
    need the state can request it explicitly through this object or the adapter.
    """

    execution_id: str
    thread_id: str | None = None
    run_id: str | None = None
    graph_id: str | None = None
    node_id: str | None = None
    checkpoint_id: str | None = None
    state: Any = None
    next_nodes: tuple[str, ...] = ()
    interrupts: tuple[Any, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckpointInfo:
    """A framework-neutral reference to a LangGraph checkpoint."""

    checkpoint_id: str | None
    thread_id: str | None
    parent_checkpoint_id: str | None = None
    created_at: str | None = None
    next_nodes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


def configurable_from(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    configurable = config.get("configurable", {})
    return configurable if isinstance(configurable, Mapping) else {}


def thread_id_from(config: Mapping[str, Any] | None) -> str | None:
    value = configurable_from(config).get("thread_id")
    return value if isinstance(value, str) and value else None


def checkpoint_id_from(config: Mapping[str, Any] | None) -> str | None:
    value = configurable_from(config).get("checkpoint_id")
    return value if isinstance(value, str) and value else None


def checkpoint_id_from_snapshot(snapshot: Any) -> str | None:
    config = getattr(snapshot, "config", None)
    value = checkpoint_id_from(config)
    if value:
        return value
    checkpoint = getattr(snapshot, "checkpoint", None)
    if isinstance(checkpoint, Mapping):
        value = checkpoint.get("id")
        if isinstance(value, str) and value:
            return value
    return None


def parent_checkpoint_id_from_snapshot(snapshot: Any) -> str | None:
    parent_config = getattr(snapshot, "parent_config", None)
    value = checkpoint_id_from(parent_config)
    return value


def checkpoint_info(snapshot: Any) -> CheckpointInfo:
    config = getattr(snapshot, "config", None)
    metadata = getattr(snapshot, "metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}
    next_nodes = getattr(snapshot, "next", ())
    if isinstance(next_nodes, str):
        next_nodes = (next_nodes,)
    else:
        try:
            next_nodes = tuple(str(value) for value in next_nodes)
        except TypeError:
            next_nodes = ()
    return CheckpointInfo(
        checkpoint_id=checkpoint_id_from_snapshot(snapshot),
        thread_id=thread_id_from(config),
        parent_checkpoint_id=parent_checkpoint_id_from_snapshot(snapshot),
        created_at=getattr(snapshot, "created_at", None),
        next_nodes=next_nodes,
        metadata=dict(metadata),
    )
