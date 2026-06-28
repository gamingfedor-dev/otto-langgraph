from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
import json
from typing import Literal
from pydantic import BaseModel, Field

class Finding(BaseModel):
    source: str = Field(description="agent name")
    summary: str = Field(description="one-line finding")
    confidence: Literal['low', 'medium', 'high'] = Field(description="confidence level")
# --- state ---
class OttoState(TypedDict):
    task: str
    findings: Annotated[list, __import__("operator").add]
    merged: str


# --- nodes ---
# paste node functions here
async def run_structured(sys_prompt: str, user_prompt: str, schema, attempts: int = 2):
    instruction = (
        f"{sys_prompt}\n\nReply with ONLY valid JSON matching this schema. "
        f"No prose, no code fences:\n{json.dumps(schema.model_json_schema())}"
    )
    for i in range(attempts):
        raw = await run_agent(instruction, user_prompt)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return schema.model_validate_json(cleaned)
        except Exception:
            if i == attempts - 1:
                raise

async def hanji(state: OttoState) -> dict:
    f = await run_structured("You are hanji, an evidence gatherer.", state["task"], Finding)
    return {"findings": [f]}


async def vault(state: OttoState) -> dict:
    f = await run_structured("You are vault, a decisions historian.", state["task"], Finding)
    return {"findings": [f]}


async def git(state: OttoState) -> dict:
    f = await run_structured("You are git, a history tracer.", state["task"], Finding)
    return {"findings": [f]}


async def merge(state: OttoState) -> dict:
    lines = [f"[{f.source} | {f.confidence}] {f.summary}" for f in state["findings"]]
    out = await run_agent("Synthesize these findings into one tight summary.", "\n".join(lines))
    return {"merged": out}

# --- graph ---
builder = StateGraph(OttoState)
for name, fn in [("hanji", hanji), ("vault", vault), ("git", git), ("merge", merge)]:
    builder.add_node(name, fn)
builder.add_edge(START, "hanji")
builder.add_edge(START, "vault")
builder.add_edge(START, "git")
builder.add_edge("hanji", "merge")
builder.add_edge("vault", "merge")
builder.add_edge("git", "merge")
builder.add_edge("merge", END)
graph = builder.compile()


# --- run ---
async def main():
    print("=== stream_mode='updates' (each node's delta as it finishes) ===")
    async for chunk in graph.astream(
        {"task": "Why does our reconnect take 8 seconds?", "findings": []},
        stream_mode="updates",
    ):
        for node, patch in chunk.items():
            print(f"[{node}] -> wrote keys: {list(patch.keys())}")
    
    print("\n=== stream_mode='values' (full state snapshot each step) ===")
    async for snapshot in graph.astream(
        {"task": "Why does our reconnect take 8 seconds?", "findings": []},
        stream_mode="values",
    ):
        print(f"state now has {len(snapshot.get('findings', []))} findings, "
              f"merged={'yes' if snapshot.get('merged') else 'no'}")


if __name__ == "__main__":
    asyncio.run(main())
