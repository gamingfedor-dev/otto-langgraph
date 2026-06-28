import json

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

NO_TOOLS = " Answer directly from your own reasoning. Do not call any tools."


def _options(system_prompt: str, max_turns: int, model: str | None) -> ClaudeAgentOptions:
    kwargs = dict(
        max_turns=max_turns,
        system_prompt=system_prompt + NO_TOOLS,
        setting_sources=[],
        allowed_tools=[],
    )
    if model:
        kwargs["model"] = model
    return ClaudeAgentOptions(**kwargs)


async def run_agent(system_prompt: str, user_prompt: str, *, max_turns: int = 6, model: str | None = None) -> str:
    chunks = []
    async for msg in query(prompt=user_prompt, options=_options(system_prompt, max_turns, model)):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks)


async def run_structured(system_prompt: str, user_prompt: str, schema, *, attempts: int = 2,
                         max_turns: int = 6, model: str | None = None):
    instruction = (
        f"{system_prompt}\n\nReply with ONLY valid JSON matching this schema. "
        f"No prose, no code fences:\n{json.dumps(schema.model_json_schema())}"
    )
    for i in range(attempts):
        raw = await run_agent(instruction, user_prompt, max_turns=max_turns, model=model)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return schema.model_validate_json(cleaned)
        except Exception:
            if i == attempts - 1:
                raise
