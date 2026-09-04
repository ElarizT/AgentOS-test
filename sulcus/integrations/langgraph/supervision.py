"""Minimal supervision bridge for LangGraph's native interrupt/resume model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from sulcus.observability import RuntimeEventLog

from .events import emit


class SupervisionError(RuntimeError):
    """A requested supervision operation is not supported by the graph."""


@dataclass(frozen=True)
class SupervisionAction:
    action: str
    execution_id: str
    status: str
    details: Mapping[str, Any] = field(default_factory=dict)


def _command(*, resume: Any = None, update: Any = None) -> Any:
    try:
        from langgraph.types import Command
    except ImportError as exc:
        raise SupervisionError(
            "LangGraph is required for supervision actions; install the adapter extra."
        ) from exc
    kwargs: dict[str, Any] = {}
    if resume is not None:
        kwargs["resume"] = resume
    if update is not None:
        kwargs["update"] = update
    return Command(**kwargs)


def resume_graph(graph: Any, config: Mapping[str, Any], value: Any, *, event_log: RuntimeEventLog, execution_id: str) -> Any:
    """Resume a graph paused by LangGraph's ``interrupt()`` mechanism."""
    emit(event_log, "langgraph.supervision.resume_requested", "LangGraph execution resume requested", {
        "execution_id": execution_id,
    })
    try:
        result = graph.invoke(_command(resume=value), config=dict(config))
    except Exception as exc:
        emit(event_log, "langgraph.supervision.resume_failed", "LangGraph execution resume failed", {
            "execution_id": execution_id,
            "error_type": type(exc).__name__,
        }, level="ERROR")
        raise
    emit(event_log, "langgraph.supervision.resumed", "LangGraph execution resumed", {
        "execution_id": execution_id,
    })
    return result


def inject_state(graph: Any, config: Mapping[str, Any], values: Any, *, event_log: RuntimeEventLog, execution_id: str) -> Any:
    """Apply an explicit state update through LangGraph's checkpoint API."""
    update_state = getattr(graph, "update_state", None)
    if not callable(update_state):
        raise SupervisionError("This LangGraph graph does not expose update_state().")
    emit(event_log, "langgraph.supervision.inject_requested", "LangGraph state injection requested", {
        "execution_id": execution_id,
    })
    result = update_state(dict(config), values)
    emit(event_log, "langgraph.supervision.injected", "LangGraph state updated", {
        "execution_id": execution_id,
    })
    return result


def require_interrupt(snapshot: Any) -> None:
    interrupts = getattr(snapshot, "interrupts", ())
    if not interrupts:
        raise SupervisionError(
            "LangGraph pause is cooperative in v1.0: the graph must already be paused "
            "at a LangGraph interrupt point."
        )
