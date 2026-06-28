from common import asyncio, TypedDict, Annotated, StateGraph, START, END, run_agent
import json
import operator
from typing import Literal
from pydantic import BaseModel
from langgraph.types import RetryPolicy


# --- schema ---
class Decision(BaseModel):
    next: Literal["o7", "rock", "devil", "done"]
    reason: str


# --- state ---
class OttoState(TypedDict):
    task: str
    history: Annotated[list, operator.add]
    next: str
    final: str


# --- structured helper ---
async def run_structured(system_prompt: str, user_prompt: str, schema, attempts: int = 2):
    instruction = (
        f"{system_prompt}\n\nReply with ONLY valid JSON matching this schema. "
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


# --- nodes ---
async def supervisor(state: OttoState, config) -> dict:
    cap = config["configurable"].get("max_specialists", 3)
    if len(state["history"]) >= cap:
        return {"next": "done"}

    done_so_far = "\n".join(f"{h['agent']}: {h['output'][:200]}" for h in state["history"]) or "nothing yet"
    decision = await run_structured(
        "You are Otto, a supervisor. Pick the next specialist for the task: "
        "o7 (implement/fix code), rock (performance), devil (adversarial review), "
        "or 'done' if the task is complete. Do not repeat work already done.",
        f"Task: {state['task']}\n\nWork done:\n{done_so_far}",
        Decision,
    )
    return {"next": decision.next}


def route(state: OttoState) -> str:
    return state["next"]


async def o7(state: OttoState) -> dict:
    out = await run_agent("You are o7, a senior engineer. Implement or fix the code. Concise.", state["task"])
    return {"history": [{"agent": "o7", "output": out}]}


async def rock(state: OttoState) -> dict:
    out = await run_agent("You are rock, a performance engineer. Find the bottleneck, explain the fix.", state["task"])
    return {"history": [{"agent": "rock", "output": out}]}


async def devil(state: OttoState) -> dict:
    last = state["history"][-1]["output"] if state["history"] else state["task"]
    out = await run_agent("You are devil. Find flaws and risks in this work. Be specific.", last)
    return {"history": [{"agent": "devil", "output": out}]}


async def finalize(state: OttoState) -> dict:
    summary = "\n\n".join(f"{h['agent']}:\n{h['output']}" for h in state["history"])
    out = await run_agent("Combine the specialists' work into one final answer.", summary)
    return {"final": out}


# --- graph ---
builder = StateGraph(OttoState)
builder.add_node("supervisor", supervisor)
builder.add_node("o7", o7, retry=RetryPolicy(max_attempts=3))
builder.add_node("rock", rock, retry=RetryPolicy(max_attempts=3))
builder.add_node("devil", devil, retry=RetryPolicy(max_attempts=3))
builder.add_node("finalize", finalize)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route,
    {"o7": "o7", "rock": "rock", "devil": "devil", "done": "finalize"},
)
builder.add_edge("o7", "supervisor")
builder.add_edge("rock", "supervisor")
builder.add_edge("devil", "supervisor")
builder.add_edge("finalize", END)
graph = builder.compile()


# --- run ---
async def main():
    r = await graph.ainvoke(
        {"task": "Make our 8-second drone reconnect faster and safer.", "history": []},
        {"recursion_limit": 20, "configurable": {"max_specialists": 3}},
    )
    print("specialists used:", [h["agent"] for h in r["history"]])
    print("\nFINAL:\n", r["final"][:700])


if __name__ == "__main__":
    asyncio.run(main())
