from common import asyncio, TypedDict, Annotated, StateGraph, START, END
import operator
from langgraph.checkpoint.memory import MemorySaver


# --- state ---
class OttoState(TypedDict):
    value: int
    log: Annotated[list, operator.add]


# --- nodes ---
def step_a(state: OttoState) -> dict:
    return {"value": 1, "log": ["a"]}


def step_b(state: OttoState) -> dict:
    return {"value": state["value"] + 10, "log": ["b"]}


def step_c(state: OttoState) -> dict:
    return {"value": state["value"] + 100, "log": ["c"]}


# --- graph ---
builder = StateGraph(OttoState)
builder.add_node("step_a", step_a)
builder.add_node("step_b", step_b)
builder.add_node("step_c", step_c)
builder.add_edge(START, "step_a")
builder.add_edge("step_a", "step_b")
builder.add_edge("step_b", "step_c")
builder.add_edge("step_c", END)
graph = builder.compile(checkpointer=MemorySaver())


# --- run ---
async def main():
    cfg = {"configurable": {"thread_id": "t1"}}
    final = await graph.ainvoke({"value": 0, "log": []}, cfg)
    print("original timeline:", final["value"], final["log"])

    history = [s async for s in graph.aget_state_history(cfg)]
    print("\ncheckpoints (newest first):")
    for s in history:
        print("  ", s.values, "next:", s.next)

    after_a = next(s for s in history if s.values.get("log") == ["a"])
    print("\nforking from:", after_a.values)

    forked_cfg = await graph.aupdate_state(after_a.config, {"value": 999})
    forked = await graph.ainvoke(None, forked_cfg)
    print("forked timeline: ", forked["value"], forked["log"])


if __name__ == "__main__":
    asyncio.run(main())
