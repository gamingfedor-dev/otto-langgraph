from .config import OttoConfig
from .graph import build_otto, OttoState
from .roster import SPECIALISTS

__all__ = ["OttoConfig", "build_otto", "OttoState", "SPECIALISTS", "run_otto"]


async def run_otto(task: str, config: OttoConfig | None = None, thread_id: str = "default") -> dict:
    config = config or OttoConfig()
    graph = build_otto(config)
    run_config = {
        "recursion_limit": config.recursion_limit,
        "configurable": {"thread_id": thread_id, "max_specialists": config.max_specialists},
    }
    return await graph.ainvoke({"task": task, "history": []}, run_config)
