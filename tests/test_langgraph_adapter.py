from __future__ import annotations

from dataclasses import dataclass

import pytest

from sulcus.integrations.langgraph import LangGraphAdapter, SupervisionError
from sulcus.observability import RuntimeEventLog


@dataclass
class Snapshot:
    values: dict
    next: tuple[str, ...] = ()
    interrupts: tuple = ()
    metadata: dict = None
    config: dict = None
    parent_config: dict | None = None
    created_at: str | None = None

    def __post_init__(self):
        self.metadata = self.metadata or {}
        self.config = self.config or {}


class FakeGraph:
    name = "fake_graph"

    def __init__(self):
        self.snapshot = Snapshot(
            values={"answer": 42},
            next=(),
            config={"configurable": {"thread_id": "t1", "checkpoint_id": "cp1"}},
            created_at="2026-09-03T09:00:00Z",
        )
        self.invocations = []
        self.updates = []

    def invoke(self, input, *, config, **kwargs):
        self.invocations.append((input, config, kwargs))
        return {"answer": 42}

    def get_state(self, config):
        return self.snapshot

    def get_state_history(self, config):
        return iter([self.snapshot])

    def update_state(self, config, values):
        self.updates.append((config, values))
        return {"configurable": {"thread_id": "t1", "checkpoint_id": "cp2"}}


def test_invoke_records_lifecycle_and_context():
    log = RuntimeEventLog()
    graph = FakeGraph()
    adapter = LangGraphAdapter(graph, event_log=log)

    assert adapter.invoke({"question": "life"}, config={"configurable": {"thread_id": "t1"}}) == {"answer": 42}
    types = [event.event_type for event in log.events]
    assert types[0] == "langgraph.run.started"
    assert "langgraph.run.completed" in types
    assert "langgraph.checkpoint.observed" in types

    context = adapter.execution_context()
    assert context.execution_id == adapter.execution_id
    assert context.thread_id == "t1"
    assert context.checkpoint_id == "cp1"
    assert context.state == {"answer": 42}


def test_checkpoint_history_is_normalized():
    adapter = LangGraphAdapter(FakeGraph())
    checkpoints = adapter.list_checkpoints({"configurable": {"thread_id": "t1"}})
    assert len(checkpoints) == 1
    assert checkpoints[0].checkpoint_id == "cp1"
    assert checkpoints[0].thread_id == "t1"


def test_inject_uses_langgraph_update_state():
    graph = FakeGraph()
    adapter = LangGraphAdapter(graph)
    adapter.inject({"answer": 43}, {"configurable": {"thread_id": "t1"}})
    assert graph.updates == [({"configurable": {"thread_id": "t1"}}, {"answer": 43})]


def test_pause_requires_existing_interrupt():
    adapter = LangGraphAdapter(FakeGraph())
    with pytest.raises(SupervisionError, match="interrupt"):
        adapter.pause({"configurable": {"thread_id": "t1"}})
