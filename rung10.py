from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
import json
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver

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
checkpointer = MemorySaver()
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
graph = builder.compile(checkpointer=checkpointer)


# --- run ---
async def main():
    cfg = {'configurable': {'thread_id': 't1'}}
    await graph.ainvoke(
        {'task': '"Why does our reconnect take 8 seconds?', 'findings': []},
        cfg
    )

    snap = await graph.aget_state(cfg)
    print("saved findings:", len(snap.values["findings"]))
    print("next nodes:   ", snap.next)        
    
    history = [s async for s in graph.aget_state_history(cfg)]
    print("checkpoints:  ", len(history))      # one per superstep — enables time travel (rung 15)

    cfg2 = {"configurable": {"thread_id": "t2"}}
    snap2 = await graph.aget_state(cfg2)
    print("t2 isolated:  ", "EMPTY" if not snap2.values else snap2.values)


if __name__ == "__main__":
    asyncio.run(main())
