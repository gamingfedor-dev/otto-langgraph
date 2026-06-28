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

async def ship(state: OttoState) -> dict:
    return {"decision": "shipped ✅"}


async def discard(state: OttoState) -> dict:
    return {"decision": "rejected ❌ — back to drawing board"}


def route_decision(state: OttoState) -> str:
    return "ship" if state["decision"].strip().lower().startswith("approve") else "discard"

# --- graph ---
builder = StateGraph(OttoState)
builder.add_node("draft", draft)              # ← MISSING
builder.add_node("human_gate", human_gate)    # ← MISSING
builder.add_node("ship", ship)
builder.add_node("discard", discard)
builder.add_edge(START, "draft")              # ← MISSING (no entry point)
builder.add_edge("draft", "human_gate")
builder.add_conditional_edges("human_gate", route_decision, {"ship": "ship", "discard": "discard"})
builder.add_edge("ship", END)
builder.add_edge("discard", END)
graph = builder.compile(checkpointer=MemorySaver())




# --- run ---
async def main():
    cfg = {"configurable": {"thread_id": "ship-1"}}
    result = await graph.ainvoke({"task": "Fix an off-by-one in a for loop"}, cfg)

    print(result["__interrupt__"][0].value["draft"])
    answer = input("approve or reject? ")          # <-- REAL human input

    final = await graph.ainvoke(Command(resume=answer), cfg)
    print("outcome:", final["decision"])

if __name__ == "__main__":
    asyncio.run(main())
