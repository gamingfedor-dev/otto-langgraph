
import asyncio
from typing import TypedDict

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query
from langgraph.graph import END, START, StateGraph


class OttoState(TypedDict):
    task: str
    route: str
    output: str

ROUTER_SYS = (
    "You are a task router. Read the task and pick ONE specialist:\n"
    "- o7 = writing, fixing, or refactoring code\n"
    "- rock = performance, profiling, latency, optimization\n"
    "Reply with EXACTLY one word: o7 or rock. No punctuation, no explanation."
)

async def run_agent(system_prompt: str, user_prompt: str) -> str:
    chunks = []
    async for msg in query(
      prompt = user_prompt,
      options=ClaudeAgentOptions(
            max_turns=10,
            system_prompt=system_prompt,
            setting_sources=[],
            allowed_tools=[],
            disallowed_tools=["Write", "Read", "Edit", "Bash", "Glob", "Grep"],
        )     
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)

    return "".join(chunks)


async def router(state: OttoState) -> dict:
    raw = await run_agent(ROUTER_SYS, state['task'])
    choice = raw.strip().lower()
    route = choice if choice in ('o7', 'rock') else 'o7'
    return {'route': route}

async def o7(state: OttoState) -> dict:
    out = await run_agent(
        "You are o7, a senior engineer. Implement or fix the code. Be concise.",
        state["task"],
    )
    return {"output": out}


async def rock(state: OttoState) -> dict:
    out = await run_agent(
        "You are rock, a performance engineer. Find the bottleneck, explain the fix.",
        state["task"],
    )
    return {"output": out}

def pick_specialist(state: OttoState) -> str:
    return state["route"]


builder = StateGraph(OttoState)
builder.add_node("router", router)
builder.add_node("o7", o7)
builder.add_node("rock", rock)

builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",            # source node
    pick_specialist,     # fn: reads state, returns a label
    {"o7": "o7", "rock": "rock"},   # label → which node to run
)
builder.add_edge("o7", END)
builder.add_edge("rock", END)
graph = builder.compile()

async def main():
    for task in [
        "Write a Python function to debounce calls",
        "My render loop drops to 12fps under load, why?",
        "Need performance update"
    ]:
        result = await graph.ainvoke({"task": task})
        print(f"\nTASK:  {task}")
        print(f"ROUTE: {result['route']}")
        print(f"OUTPUT:\n{result['output'][:400]}")

if __name__ == "__main__":
    asyncio.run(main())
