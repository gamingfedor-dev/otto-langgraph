import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    async for msg in query(
        prompt="Say hi in 5 words",
        options=ClaudeAgentOptions(max_turns=1),
    ):
        print(type(msg).__name__, msg)


if __name__ == "__main__":
    asyncio.run(main())
