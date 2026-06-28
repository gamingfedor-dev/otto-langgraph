import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from .config import OttoConfig
from .roster import SPECIALISTS
from .schemas import Decision
from .sdk import run_agent, run_structured


class OttoState(TypedDict):
    task: str
    history: Annotated[list, operator.add]
    next: str
    final: str


def _make_supervisor(settings: OttoConfig):
    roster = ", ".join(SPECIALISTS)

    async def supervisor(state: OttoState, config) -> dict:
        cap = config["configurable"].get("max_specialists", settings.max_specialists)
        if len(state["history"]) >= cap:
            return {"next": "done"}

        done = "\n".join(f"{h['agent']}: {h['output'][:200]}" for h in state["history"]) or "nothing yet"
        decision = await run_structured(
            f"You are Otto, an orchestrator. Pick the next specialist from: {roster}, or 'done' "
            "if the task is complete. Do not repeat work already done.",
            f"Task: {state['task']}\n\nWork done:\n{done}",
            Decision,
            max_turns=settings.max_turns,
            model=settings.model,
        )
        choice = decision.next if decision.next in SPECIALISTS or decision.next == "done" else "done"
        return {"next": choice}

    return supervisor


def _make_specialist(name: str, config: OttoConfig):
    system_prompt = SPECIALISTS[name]

    async def specialist(state: OttoState) -> dict:
        prior = state["history"][-1]["output"] if state["history"] else ""
        prompt = state["task"] if not prior else f"{state['task']}\n\nPrior work:\n{prior}"
        out = await run_agent(system_prompt, prompt, max_turns=config.max_turns, model=config.model)
        return {"history": [{"agent": name, "output": out}]}

    return specialist


def _make_finalize(config: OttoConfig):
    async def finalize(state: OttoState) -> dict:
        summary = "\n\n".join(f"{h['agent']}:\n{h['output']}" for h in state["history"]) or state["task"]
        out = await run_agent(
            "You are Otto. Combine the specialists' work into one final answer.",
            summary,
            max_turns=config.max_turns,
            model=config.model,
        )
        return {"final": out}

    return finalize


def _route(state: OttoState) -> str:
    return state["next"] if state["next"] in SPECIALISTS else "finalize"


def build_otto(config: OttoConfig | None = None):
    config = config or OttoConfig()
    builder = StateGraph(OttoState)

    builder.add_node("supervisor", _make_supervisor(config))
    builder.add_node("finalize", _make_finalize(config))
    for name in SPECIALISTS:
        builder.add_node(name, _make_specialist(name, config),
                         retry_policy=RetryPolicy(max_attempts=config.retry_attempts))

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        _route,
        {**{name: name for name in SPECIALISTS}, "finalize": "finalize"},
    )
    for name in SPECIALISTS:
        builder.add_edge(name, "supervisor")
    builder.add_edge("finalize", END)

    checkpointer = MemorySaver() if config.persist else None
    store = InMemoryStore() if config.persist else None
    return builder.compile(checkpointer=checkpointer, store=store)
