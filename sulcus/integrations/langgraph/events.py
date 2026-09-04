"""LangGraph -> Sulcus event normalization for the v1 adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sulcus.observability import RuntimeEvent, RuntimeEventLog


_SOURCE = "LangGraphAdapter"
_SAFE_METADATA_KEYS = {
    "langgraph_node",
    "langgraph_step",
    "langgraph_triggers",
    "checkpoint_ns",
    "thread_id",
    "graph_id",
    "execution_id",
    "run_id",
    "parent_run_id",
}


def _safe_value(value: Any) -> str | int | float | bool | None:
    if isinstance(value, (str, int, float, bool)) and len(str(value)) <= 200:
        return value
    return None


def safe_callback_metadata(metadata: Mapping[str, Any] | None, **extra: Any) -> dict[str, Any]:
    """Keep only small routing identifiers; never copy model/tool payloads."""
    result: dict[str, Any] = {}
    if metadata:
        for key in _SAFE_METADATA_KEYS:
            value = _safe_value(metadata.get(key))
            if value is not None:
                result[key] = value
    for key, value in extra.items():
        safe = _safe_value(value)
        if safe is not None:
            result[key] = safe
    return result


def emit(
    event_log: RuntimeEventLog,
    event_type: str,
    message: str,
    metadata: Mapping[str, Any] | None = None,
    *,
    level: str = "INFO",
) -> RuntimeEvent:
    """Create and append one normalized Sulcus runtime event."""
    factory = {
        "INFO": RuntimeEvent.info,
        "WARNING": RuntimeEvent.warning,
        "ERROR": RuntimeEvent.error,
        "DEBUG": RuntimeEvent.debug,
    }[level]
    event = factory(_SOURCE, event_type, message, dict(metadata or {}))
    event_log.append(event)
    return event


def runnable_name(serialized: Mapping[str, Any] | None, fallback: str = "runnable") -> str:
    if serialized:
        name = serialized.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
        identifier = serialized.get("id")
        if isinstance(identifier, (list, tuple)) and identifier:
            value = identifier[-1]
            if isinstance(value, str) and value.strip():
                return value.strip()
    return fallback
