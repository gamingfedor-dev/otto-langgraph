from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
import operator


# --- state ---
class OttoState(TypedDict):
    task: str
    findings: Annotated[list, operator.add]
    merged: str
    headline: str


# --- nodes ---
async def hanji(state: OttoState) -> dict:
    out = await run_agent("You are hanji. Gather code-reference evidence. Bullet list.", state["task"])
    return {"findings": [f"hanji:\n{out}"]}


async def vault(state: OttoState) -> dict:
    out = await run_agent("You are vault. Find prior decisions and docs. Bullet list.", state["task"])
    return {"findings": [f"vault:\n{out}"]}


async def merge(state: OttoState) -> dict:
    out = await run_agent("Synthesize these findings into one tight summary.", "\n\n".join(state["findings"]))
    return {"merged": out}


async def headline(state: OttoState) -> dict:
    out = await run_agent("Turn this summary into a one-line headline.", state["merged"])
    return {"headline": out}


# --- graph ---
sub = StateGraph(OttoState)
sub.add_node("hanji", hanji)
sub.add_node("vault", vault)
sub.add_node("merge", merge)
sub.add_edge(START, "hanji")
sub.add_edge(START, "vault")
sub.add_edge("hanji", "merge")
sub.add_edge("vault", "merge")
sub.add_edge("merge", END)
research = sub.compile()

parent = StateGraph(OttoState)
parent.add_node("research", research)
parent.add_node("headline", headline)
parent.add_edge(START, "research")
parent.add_edge("research", "headline")
parent.add_edge("headline", END)
graph = parent.compile()


# --- run ---
async def main():
    r = await graph.ainvoke({"task": "Why does our reconnect take 8 seconds?", "findings": []})
    print("findings:", len(r["findings"]))
    print("HEADLINE:", r["headline"])


if __name__ == "__main__":
    asyncio.run(main())
