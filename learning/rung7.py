import operator

from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent


# --- state ---
class OttoState(TypedDict):
    task: str
    findings: Annotated[list, operator.add]
    merged: str


# --- nodes ---
# paste node functions here
async def hanji(state: OttoState) -> dict:
    out = await run_agent("You are hanji. Gather code-reference evidence. Bullet list.", state["task"])
    return {"findings": [f"hanji:\n{out}"]}


async def vault(state: OttoState) -> dict:
    out = await run_agent("You are vault. Find prior decisions and docs. Bullet list.", state["task"])
    return {"findings": [f"vault:\n{out}"]}


async def git(state: OttoState) -> dict:
    out = await run_agent("You are git. Trace history and blame angles. Bullet list.", state["task"])
    return {"findings": [f"git:\n{out}"]}


async def merge(state: OttoState) -> dict:
    combined = "\n\n".join(state["findings"])
    out = await run_agent("Synthesize these findings into one tight summary.", combined)
    return {"merged": out}

# --- graph ---
builder = StateGraph(OttoState)
# paste add_node / add_edge wiring here
builder.add_node("hanji", hanji)
builder.add_node("vault", vault)
builder.add_node("git", git)
builder.add_node("merge", merge)

builder.add_edge(START, "hanji")
builder.add_edge(START, "vault")
builder.add_edge(START, "git")
builder.add_edge("hanji", "merge")
builder.add_edge("vault", "merge")
builder.add_edge("git", "merge")
builder.add_edge("merge", END)
graph = builder.compile()


# --- run ---
async def main():
    r = await graph.ainvoke({"task": "Why does our reconnect take 8 seconds?", "findings": []})
    print("COUNT:", len(r["findings"]))      # 3 — proves the reducer merged all three
    print("MERGED:\n", r["merged"][:600])


if __name__ == "__main__":
    asyncio.run(main())
