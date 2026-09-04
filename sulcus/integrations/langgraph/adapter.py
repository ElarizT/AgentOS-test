"""Minimal viable LangGraph adapter for Sulcus v1.0."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from sulcus.observability import RuntimeEventLog

from .context import (
    CheckpointInfo,
    ExecutionContext,
    checkpoint_id_from,
    checkpoint_info,
    configurable_from,
    thread_id_from,
)
from .events import emit
from .supervision import SupervisionAction, SupervisionError, inject_state, require_interrupt, resume_graph


@dataclass
class _RunTracker:
    execution_id: str
    run_id: str | None = None


class LangGraphAdapter:
    """Bridge a compiled LangGraph graph into Sulcus observability/context APIs.

    v1.0 deliberately delegates execution, persistence, and checkpointing to
    LangGraph. Sulcus normalizes what LangGraph exposes and provides a small
    supervision facade for native interrupt/resume and state-update operations.
    """

    def __init__(
        self,
        graph: Any,
        *,
        event_log: RuntimeEventLog | None = None,
        execution_id: str | None = None,
        graph_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if graph is None:
            raise TypeError("graph is required")
        self.graph = graph
        self.event_log = event_log or RuntimeEventLog()
        self.execution_id = execution_id or uuid4().hex
        self.graph_id = graph_id or getattr(graph, "name", None) or type(graph).__name__
        self.metadata = dict(metadata or {})
        self._last_config: dict[str, Any] = {}
        self._last_result: Any = None
        self._tracker = _RunTracker(self.execution_id)

    def invoke(self, input: Any, config: Mapping[str, Any] | None = None, **kwargs: Any) -> Any:
        """Execute the graph once and capture Sulcus-normalized lifecycle events."""
        run_config = self._prepare_config(config)
        emit(self.event_log, "langgraph.run.started", "LangGraph execution started", self._run_metadata(run_config))
        callback = _build_callback_handler(self.event_log, self.execution_id, self.graph_id, self._tracker)
        if callback is not None:
            run_config = _add_callback(run_config, callback)
        try:
            self._last_result = self.graph.invoke(input, config=run_config, **kwargs)
        except Exception as exc:
            emit(self.event_log, "langgraph.run.failed", "LangGraph execution failed", {
                **self._run_metadata(run_config),
                "error_type": type(exc).__name__,
            }, level="ERROR")
            raise
        finally:
            self._refresh_context(run_config)
        emit(self.event_log, "langgraph.run.completed", "LangGraph execution completed", self._run_metadata(run_config))
        return self._last_result

    async def ainvoke(self, input: Any, config: Mapping[str, Any] | None = None, **kwargs: Any) -> Any:
        """Async counterpart to :meth:`invoke`."""
        run_config = self._prepare_config(config)
        emit(self.event_log, "langgraph.run.started", "LangGraph execution started", self._run_metadata(run_config))
        callback = _build_callback_handler(self.event_log, self.execution_id, self.graph_id, self._tracker)
        if callback is not None:
            run_config = _add_callback(run_config, callback)
        try:
            method = getattr(self.graph, "ainvoke", None)
            if not callable(method):
                raise TypeError("The supplied LangGraph graph does not expose ainvoke().")
            self._last_result = await method(input, config=run_config, **kwargs)
        except Exception as exc:
            emit(self.event_log, "langgraph.run.failed", "LangGraph execution failed", {
                **self._run_metadata(run_config),
                "error_type": type(exc).__name__,
            }, level="ERROR")
            raise
        finally:
            self._refresh_context(run_config)
        emit(self.event_log, "langgraph.run.completed", "LangGraph execution completed", self._run_metadata(run_config))
        return self._last_result

    def execution_context(self, config: Mapping[str, Any] | None = None) -> ExecutionContext:
        """Return the latest Sulcus execution view, including current state."""
        selected = dict(config or self._last_config)
        state = self._get_state(selected)
        snapshot = state
        next_nodes = getattr(snapshot, "next", ()) if snapshot is not None else ()
        if isinstance(next_nodes, str):
            next_nodes = (next_nodes,)
        else:
            try:
                next_nodes = tuple(str(value) for value in next_nodes)
            except TypeError:
                next_nodes = ()
        interrupts = getattr(snapshot, "interrupts", ()) if snapshot is not None else ()
        if interrupts is None:
            interrupts = ()
        else:
            try:
                interrupts = tuple(interrupts)
            except TypeError:
                interrupts = ()
        metadata = getattr(snapshot, "metadata", {}) if snapshot is not None else {}
        if not isinstance(metadata, Mapping):
            metadata = {}
        return ExecutionContext(
            execution_id=self.execution_id,
            thread_id=thread_id_from(selected),
            run_id=self._tracker.run_id,
            graph_id=self.graph_id,
            checkpoint_id=self.checkpoint(config=selected),
            state=getattr(snapshot, "values", None) if snapshot is not None else None,
            next_nodes=next_nodes,
            interrupts=interrupts,
            metadata=dict(metadata),
        )

    def checkpoint(self, config: Mapping[str, Any] | None = None) -> str | None:
        """Return the current LangGraph checkpoint ID, if the graph has one."""
        selected = dict(config or self._last_config)
        snapshot = self._get_state(selected)
        return None if snapshot is None else checkpoint_info(snapshot).checkpoint_id

    def checkpoint_info(self, config: Mapping[str, Any] | None = None) -> CheckpointInfo | None:
        selected = dict(config or self._last_config)
        snapshot = self._get_state(selected)
        return None if snapshot is None else checkpoint_info(snapshot)

    def list_checkpoints(self, config: Mapping[str, Any] | None = None) -> list[CheckpointInfo]:
        """Return checkpoint references from LangGraph's native history."""
        selected = dict(config or self._last_config)
        history = getattr(self.graph, "get_state_history", None)
        if not callable(history):
            raise SupervisionError("This LangGraph graph does not expose get_state_history().")
        return [checkpoint_info(snapshot) for snapshot in history(dict(selected))]

    def pause(self, config: Mapping[str, Any] | None = None) -> SupervisionAction:
        """Report/validate a cooperative LangGraph interrupt pause."""
        selected = dict(config or self._last_config)
        snapshot = self._get_state(selected)
        if snapshot is None:
            raise SupervisionError("No LangGraph execution state is available to pause.")
        require_interrupt(snapshot)
        emit(self.event_log, "langgraph.supervision.paused", "LangGraph execution is paused at an interrupt", {
            "execution_id": self.execution_id,
        })
        return SupervisionAction("pause", self.execution_id, "paused", {"checkpoint_id": self.checkpoint(selected)})

    def resume(self, value: Any, config: Mapping[str, Any] | None = None) -> Any:
        return resume_graph(
            self.graph,
            dict(config or self._last_config),
            value,
            event_log=self.event_log,
            execution_id=self.execution_id,
        )

    def inject(self, values: Any, config: Mapping[str, Any] | None = None) -> Any:
        return inject_state(
            self.graph,
            dict(config or self._last_config),
            values,
            event_log=self.event_log,
            execution_id=self.execution_id,
        )

    def approve(self, value: Any = True, config: Mapping[str, Any] | None = None) -> Any:
        """Resume an interrupted graph with an approval value."""
        emit(self.event_log, "langgraph.supervision.approval_granted", "LangGraph supervision approval granted", {
            "execution_id": self.execution_id,
        })
        return self.resume(value, config)

    def deny(self, value: Any = False, config: Mapping[str, Any] | None = None) -> Any:
        """Resume an interrupted graph with a denial value.

        The application decides how a False/denial value changes graph control.
        v1.0 does not invent a policy engine around LangGraph.
        """
        emit(self.event_log, "langgraph.supervision.approval_denied", "LangGraph supervision approval denied", {
            "execution_id": self.execution_id,
        }, level="WARNING")
        return self.resume(value, config)

    def cancel(self) -> SupervisionAction:
        raise SupervisionError(
            "LangGraph has no framework-neutral cancellation primitive exposed by the v1 adapter."
        )

    def events(self, limit: int | None = None):
        return self.event_log.latest(limit)

    def _prepare_config(self, config: Mapping[str, Any] | None) -> dict[str, Any]:
        selected = dict(config or {})
        self._last_config = selected
        return selected

    def _run_metadata(self, config: Mapping[str, Any]) -> dict[str, Any]:
        metadata = {
            "execution_id": self.execution_id,
            "graph_id": self.graph_id,
        }
        thread_id = thread_id_from(config)
        if thread_id:
            metadata["thread_id"] = thread_id
        if self._tracker.run_id:
            metadata["run_id"] = self._tracker.run_id
        return metadata

    def _get_state(self, config: Mapping[str, Any]) -> Any | None:
        method = getattr(self.graph, "get_state", None)
        if not callable(method):
            return None
        try:
            return method(dict(config))
        except (TypeError, ValueError):
            return None

    def _refresh_context(self, config: Mapping[str, Any]) -> None:
        self._last_config = dict(config)
        snapshot = self._get_state(config)
        if snapshot is not None:
            info = checkpoint_info(snapshot)
            if info.checkpoint_id:
                emit(self.event_log, "langgraph.checkpoint.observed", "LangGraph checkpoint observed", {
                    "execution_id": self.execution_id,
                    "checkpoint_id": info.checkpoint_id,
                    "thread_id": info.thread_id,
                })


def _add_callback(config: Mapping[str, Any], callback: Any) -> dict[str, Any]:
    result = dict(config)
    callbacks = result.get("callbacks", [])
    if callbacks is None:
        callbacks = []
    elif not isinstance(callbacks, (list, tuple)):
        callbacks = [callbacks]
    else:
        callbacks = list(callbacks)
    callbacks.append(callback)
    result["callbacks"] = callbacks
    return result


def _build_callback_handler(event_log: RuntimeEventLog, execution_id: str, graph_id: str, tracker: _RunTracker) -> Any | None:
    try:
        from langchain_core.callbacks import BaseCallbackHandler
    except ImportError:
        return None

    class _SulcusLangGraphCallbackHandler(BaseCallbackHandler):
        raise_error = False
        run_inline = True

        def _meta(self, kwargs: Mapping[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
            from .events import safe_callback_metadata
            metadata = kwargs.get("metadata", {}) if isinstance(kwargs, Mapping) else {}
            return safe_callback_metadata(metadata, execution_id=execution_id, graph_id=graph_id, **extra)

        def on_chain_start(self, serialized: Mapping[str, Any], inputs: Any, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            from .events import runnable_name
            run_id_text = str(run_id)
            if tracker.run_id is None:
                tracker.run_id = run_id_text
            meta = self._meta(kwargs, run_id=run_id_text, parent_run_id=str(parent_run_id) if parent_run_id else None)
            node = meta.get("langgraph_node")
            if node:
                emit(event_log, "langgraph.node.started", "LangGraph node started", meta)
            else:
                meta["runnable"] = runnable_name(serialized)
                emit(event_log, "langgraph.chain.started", "LangGraph chain started", meta)

        def on_chain_end(self, outputs: Any, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            meta = self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None)
            if meta.get("langgraph_node"):
                emit(event_log, "langgraph.node.completed", "LangGraph node completed", meta)
            else:
                emit(event_log, "langgraph.chain.completed", "LangGraph chain completed", meta)

        def on_chain_error(self, error: BaseException, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            meta = self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None, error_type=type(error).__name__)
            if meta.get("langgraph_node"):
                emit(event_log, "langgraph.node.failed", "LangGraph node failed", meta, level="ERROR")
            else:
                emit(event_log, "langgraph.chain.failed", "LangGraph chain failed", meta, level="ERROR")

        def on_llm_start(self, serialized: Mapping[str, Any], prompts: list[str], *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            from .events import runnable_name
            emit(event_log, "langgraph.llm.started", "LangGraph LLM call started", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None, model=runnable_name(serialized)))

        def on_chat_model_start(self, serialized: Mapping[str, Any], messages: list[Any], *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> Any:
            from .events import runnable_name
            emit(event_log, "langgraph.llm.started", "LangGraph chat model call started", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None, model=runnable_name(serialized)))

        def on_llm_end(self, response: Any, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            emit(event_log, "langgraph.llm.completed", "LangGraph LLM call completed", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None))

        def on_llm_error(self, error: BaseException, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            emit(event_log, "langgraph.llm.failed", "LangGraph LLM call failed", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None, error_type=type(error).__name__), level="ERROR")

        def on_tool_start(self, serialized: Mapping[str, Any], input_str: str, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            from .events import runnable_name
            emit(event_log, "langgraph.tool.started", "LangGraph tool call started", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None, tool_name=runnable_name(serialized)))

        def on_tool_end(self, output: Any, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            emit(event_log, "langgraph.tool.completed", "LangGraph tool call completed", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None))

        def on_tool_error(self, error: BaseException, *, run_id: Any, parent_run_id: Any = None, **kwargs: Any) -> None:
            emit(event_log, "langgraph.tool.failed", "LangGraph tool call failed", self._meta(kwargs, run_id=str(run_id), parent_run_id=str(parent_run_id) if parent_run_id else None, error_type=type(error).__name__), level="ERROR")

    return _SulcusLangGraphCallbackHandler()
