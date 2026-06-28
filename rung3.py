import asyncio
from typing import TypedDict

from claude_agent_sdk import AssistantMessage, TextBlock, query, ClaudeAgentOptions
from langgraph.graph import END, START, StateGraph

class OttoState(TypedDict):
    task: str
    plan: str
    output: str

async def run_agent(system_prompt: str, user_prompt: str) -> str:
    chunks = []
    async for msg in query(
      prompt = user_prompt,
      options=ClaudeAgentOptions(
            max_turns=2,
            system_prompt=system_prompt,
            setting_sources=[],
            allowed_tools=[]
        )     
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)

    return "".join(chunks)

async def planner(state: OttoState) -> dict:
    plan = await run_agent(
        "You are a planner. Output a short numbered plan. No prose.",
        state["task"],
    )
    return {"plan": plan}


async def executor(state: OttoState) -> dict:
    output = await run_agent(
        "You are an executor. Follow the plan. Be concise.",
        f"Task: {state['task']}\n\nPlan:\n{state['plan']}",
    )
    return {"output": output}

builder = StateGraph(OttoState)
builder.add_node("planner", planner)
builder.add_node("executor", executor)
builder.add_edge(START, "planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", END)
graph = builder.compile()

async def main():
    result = await graph.ainvoke({"task": "Reverse a linked list in Python"})
    print("PLAN:\n", result["plan"])
    print("\nOUTPUT:\n", result["output"])

if __name__ == "__main__":
    asyncio.run(main())
