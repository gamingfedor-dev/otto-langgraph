from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent


# --- state ---
class OttoState(TypedDict):
    task: str
    hanji: str
    git: str
    vault: str
    merged: str


# --- nodes ---
# paste node functions here
async def hanji(state: OttoState) -> dict:
    out = await run_agent("You are hanji. Gather code-reference evidence. Bullet list.", state["task"])
    return {"hanji": out}

async def git(state: OttoState) -> dict:
    out = await run_agent("You are git. Trace history and blame angles. Bullet list.", state["task"])
    return {"git": out}

async def vault(state: OttoState) -> dict:
    out = await run_agent("You are vault. Find prio decisions and doc. Bullet list.", state["task"])
    return {"vault": out}

async def merge(state: OttoState) -> dict:
    combined = (
        f"hanji:\n{state['hanji']}\n\n"
        f"vault:\n{state['vault']}\n\n"
        f"git:\n{state['git']}"
    )
    out = await run_agent("Synthesize these three findings in one tight summary", combined)
    return {"merged": out}
# --- graph ---
builder = StateGraph(OttoState)
builder.add_node('hanji', hanji)
builder.add_node('git', git)
builder.add_node('vault', vault)
builder.add_edge(START, 'hanji')
builder.add_edge(START, 'git')
builder.add_edge(START, 'vault')
builder.add_node('merge', merge)
builder.add_edge('hanji', 'merge')
builder.add_edge('git', 'merge')
builder.add_edge('vault', 'merge')
builder.add_edge('merge', END)
# paste add_node / add_edge wiring here
graph = builder.compile()


# --- run ---
async def main():
    r = await graph.ainvoke({"task": "Why does our reconnect take 8 seconds?"})
    print("MERGED:\n", r["merged"][:600])


if __name__ == "__main__":
    asyncio.run(main())
