from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
import operator
from langgraph.types import Send


# --- state ---
class OttoState(TypedDict):
    task: str
    subtasks: list
    results: Annotated[list, operator.add]
    final: str


# --- nodes ---
async def plan(state: OttoState) -> dict:
    raw = await run_agent(
        "Break this question into 3 distinct sub-questions. One per line, no numbering.",
        state["task"],
    )
    subs = [line.strip("-* ").strip() for line in raw.splitlines() if line.strip()][:5]
    return {"subtasks": subs}


def fan_out(state: OttoState) -> list:
    return [Send("worker", {"subtask": s}) for s in state["subtasks"]]


async def worker(state: dict) -> dict:
    out = await run_agent("Answer this sub-question concisely.", state["subtask"])
    return {"results": [out]}


async def reduce(state: OttoState) -> dict:
    out = await run_agent("Combine these answers into one tight summary.", "\n\n".join(state["results"]))
    return {"final": out}


# --- graph ---
builder = StateGraph(OttoState)
builder.add_node("plan", plan)
builder.add_node("worker", worker)
builder.add_node("reduce", reduce)
builder.add_edge(START, "plan")
builder.add_conditional_edges("plan", fan_out, ["worker"])
builder.add_edge("worker", "reduce")
builder.add_edge("reduce", END)
graph = builder.compile()


# --- run ---
async def main():
    r = await graph.ainvoke({"task": "What makes a network reconnect slow?", "subtasks": [], "results": []})
    print("subtasks:", len(r["subtasks"]))
    print("results: ", len(r["results"]))
    print("FINAL:\n", r["final"][:500])


if __name__ == "__main__":
    asyncio.run(main())
