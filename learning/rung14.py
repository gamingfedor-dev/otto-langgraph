from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver


# --- state ---
class OttoState(TypedDict):
    task: str
    reply: str


# --- nodes ---
async def agent(state: OttoState, *, store) -> dict:
    ns = ("memory", "user")
    known = await store.asearch(ns)
    facts = "\n".join(item.value["text"] for item in known) or "nothing yet"

    reply = await run_agent(
        f"Known facts about the user:\n{facts}\n\nRespond to their message briefly.",
        state["task"],
    )

    await store.aput(ns, str(len(known)), {"text": state["task"]})
    return {"reply": reply}


# --- graph ---
store = InMemoryStore()
builder = StateGraph(OttoState)
builder.add_node("agent", agent)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)
graph = builder.compile(checkpointer=MemorySaver(), store=store)


# --- run ---
async def main():
    await graph.ainvoke(
        {"task": "Remember I work on a drone ground-control app in Qt and QML."},
        {"configurable": {"thread_id": "A"}},
    )

    r = await graph.ainvoke(
        {"task": "What do I work on?"},
        {"configurable": {"thread_id": "B"}},
    )
    print("thread B reply:\n", r["reply"])


if __name__ == "__main__":
    asyncio.run(main())
