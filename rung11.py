from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

# --- state ---
class OttoState(TypedDict):
    task: str
    draft: str
    decision: str


# --- nodes ---
# paste node functions here
async def draft(state: OttoState) -> dict:
    out = await run_agent("You are o7. Draft a short code fix. Be brief.", state["task"])
    return {"draft": out}

def human_gate(state: OttoState) -> dict:
    answer = interrupt({
        "draft": state["draft"][:300],
        "question": "Approve this draft? reply approve or reject",
    })
    return {"decision": answer}

# --- graph ---
builder = StateGraph(OttoState)
builder.add_node("draft", draft)
builder.add_node("human_gate", human_gate)
builder.add_edge(START, "draft")
builder.add_edge("draft", "human_gate")
builder.add_edge("human_gate", END)
graph = builder.compile(checkpointer=MemorySaver())


# --- run ---
async def main():
    cfg = {'configurable': {'thread_id': 'ship-1'}}

    result = await graph.ainvoke({'task': 'Fix an off-by-one in a for loop'}, cfg)
    print("=== PAUSED ===")
    print("interrupt payload:", result["__interrupt__"][0].value)

    final = await graph.ainvoke(Command(resume="approve"), cfg)
    print("=== RESUMED ===")
    print("decision:", final["decision"])


if __name__ == "__main__":
    asyncio.run(main())
