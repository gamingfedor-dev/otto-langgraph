import asyncio
from typing import TypedDict
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
from langgraph.graph import StateGraph, START, END


class OttoState(TypedDict):
    task: str
    output: str


async def run_node(state: OttoState) -> dict:
    chunks = []
    async for msg in query(
        prompt=state['task'],
        options=ClaudeAgentOptions(max_turns=1)
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return {"output": "".join(chunks)}

builder = StateGraph(OttoState)
builder.add_node("agent", run_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

graph = builder.compile()

async def main():
    result = await graph.ainvoke({"task": "Say hi in 5 words"})
    print(result["output"])


if __name__ == "__main__":
    asyncio.run(main())