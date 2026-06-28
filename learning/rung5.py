import asyncio
from typing import TypedDict

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query
from langgraph.graph import END, START, StateGraph


class OttoState(TypedDict):
    task: str
    route: str
    output: str
    verdict: str
    notes: str
    revisions: str

ROUTER_SYS = (
    "You are a task router. Read the task and pick ONE specialist:\n"
    "- o7 = writing, fixing, or refactoring code\n"
    "- rock = performance, profiling, latency, optimization\n"
    "Reply with EXACTLY one word: o7 or rock. No punctuation, no explanation."
)

DEVIL_SYS = (
    "You are devil, an adversarial reviewer. Judge the solution.\n"
    "If it has a real flaw, reply: REVISE: <one line why>.\n"
    "If it is solid, reply: APPROVE.\n"
    "Reply with only that, nothing else."
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


def pick_specialist(state: OttoState) -> str:
    return state["route"]

async def o7(state: OttoState) -> dict:
    prompt = state['task']
    if state.get('verdict') == 'revise':
        prompt += f"\n\nReviewer feedback to fix:\n{state['notes']}"
    out = await run_agent(
        "You are o7, a senior engineer. Implement or fix the code. Be concise.",
        prompt,
    )
    return {"output": out}

async def rock(state: OttoState) -> dict:
    prompt = state['task']
    if state.get('verdict') == 'revise':
        prompt += f"\n\nReviewer feedback to fix:\n{state['notes']}"
    out = await run_agent(
        "You are rock, a performance engineer. Find the bottleneck, explain the fix.",
        state["task"],
    )
    return {"output": out}

async def devil(state: OttoState) -> dict:
    review = await run_agent(
        DEVIL_SYS,
        f"Task: {state['task']}\n\nSolution:\n{state['output']}",
    )
    verdict = "revise" if review.strip().upper().startswith("REVISE") else "approved"
    return {
        "verdict": verdict,
        "notes": review.strip(),
        "revisions": state.get("revisions", 0) + 1,
    }


def after_devil(state: OttoState) -> str:
    if state["verdict"] == "approved" or state["revisions"] >= 2:
        return "done"
    return state["route"]

builder = StateGraph(OttoState)
builder.add_node('router', router)
builder.add_node('o7', o7)
builder.add_node('rock', rock)
builder.add_node('devil', devil)
builder.add_conditional_edges('router', pick_specialist,
    {'o7': 'o7', 'rock': 'rock'}
)
builder.add_edge(START, 'router')
builder.add_edge('o7', 'devil')
builder.add_edge('rock', 'devil')
builder.add_conditional_edges('devil', after_devil,
    {"o7": "o7", "rock": "rock", "done": END}
)
graph = builder.compile()

async def main():
    result = await graph.ainvoke(
        {"task": "Write a thread-safe LRU cache in Python", "revisions": 0},
        {"recursion_limit": 15},
    )
    print(f"ROUTE:    {result['route']}")
    print(f"VERDICT:  {result['verdict']}")
    print(f"REVISIONS:{result['revisions']}")
    print(f"OUTPUT:\n{result['output'][:500]}")

if __name__ == "__main__":
    asyncio.run(main())