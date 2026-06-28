import operator
from dataclasses import replace
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .config import OttoConfig
from .graph import build_otto


class ChatState(TypedDict):
    messages: Annotated[list, operator.add]


def _render(messages: list) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


def build_chat(config: OttoConfig | None = None):
    config = config or OttoConfig()
    inner = build_otto(replace(config, persist=False))
    inner_config = {
        "recursion_limit": config.recursion_limit,
        "configurable": {"thread_id": "inner", "max_specialists": config.max_specialists},
    }

    async def otto_turn(state: ChatState) -> dict:
        context = _render(state["messages"])
        result = await inner.ainvoke({"task": context, "history": []}, inner_config)
        return {"messages": [{"role": "assistant", "content": result["final"]}]}

    builder = StateGraph(ChatState)
    builder.add_node("otto", otto_turn)
    builder.add_edge(START, "otto")
    builder.add_edge("otto", END)
    return builder.compile(checkpointer=MemorySaver())


async def chat(config: OttoConfig | None = None, thread_id: str = "chat-1"):
    graph = build_chat(config)
    cfg = {"configurable": {"thread_id": thread_id}}
    print("otto chat. type 'exit' to quit.\n")
    while True:
        try:
            msg = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not msg or msg.lower() in ("exit", "quit"):
            break
        result = await graph.ainvoke({"messages": [{"role": "user", "content": msg}]}, cfg)
        print("\notto>", result["messages"][-1]["content"], "\n")
