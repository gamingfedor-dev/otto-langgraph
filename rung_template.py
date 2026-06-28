from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent


# --- state ---
class OttoState(TypedDict):
    task: str


# --- nodes ---
# paste node functions here


# --- graph ---
builder = StateGraph(OttoState)
# paste add_node / add_edge wiring here
graph = builder.compile()


# --- run ---
async def main():
    r = await graph.ainvoke({"task": "..."})
    print(r)


if __name__ == "__main__":
    asyncio.run(main())
