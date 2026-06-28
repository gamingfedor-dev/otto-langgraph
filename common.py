import asyncio
from typing import TypedDict, Annotated
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
from langgraph.graph import StateGraph, START, END

__all__ = [
    "asyncio", "TypedDict", "Annotated",
    "StateGraph", "START", "END",
    "run_agent",
]


async def run_agent(system_prompt: str, user_prompt: str, max_turns: int = 2) -> str:
    chunks = []
    async for msg in query(
        prompt=user_prompt,
        options=ClaudeAgentOptions(
            max_turns=max_turns,
            system_prompt=system_prompt,
            setting_sources=[],
            allowed_tools=[],
        ),
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks)
