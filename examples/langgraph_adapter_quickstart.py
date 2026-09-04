"""Minimal LangGraph -> Sulcus adapter example.

Install the optional integration dependency first:
    pip install -e '.[langgraph]'

The graph below is intentionally small. A real LangGraph application can pass
its compiled graph directly to LangGraphAdapter.
"""

from sulcus.integrations.langgraph import LangGraphAdapter


def main() -> None:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise SystemExit("Install the LangGraph extra: pip install -e '.[langgraph]'") from exc

    def answer(state: dict) -> dict:
        return {"answer": state["a"] + state["b"]}

    builder = StateGraph(dict)
    builder.add_node("answer", answer)
    builder.add_edge(START, "answer")
    builder.add_edge("answer", END)
    graph = builder.compile()

    adapter = LangGraphAdapter(graph)
    result = adapter.invoke({"a": 20, "b": 22})
    print(result)
    for event in adapter.events():
        print(event.event_type, event.metadata)


if __name__ == "__main__":
    main()
