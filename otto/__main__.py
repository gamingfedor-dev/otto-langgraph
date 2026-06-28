import argparse
import asyncio

from . import OttoConfig, run_otto


def main():
    parser = argparse.ArgumentParser(prog="otto", description="Otto multi-agent orchestrator")
    parser.add_argument("task", nargs="?", help="the task to orchestrate (omit with --chat)")
    parser.add_argument("--chat", action="store_true", help="interactive multi-turn chat")
    parser.add_argument("--model", default=None, help="Claude model id (default: SDK default)")
    parser.add_argument("--max-specialists", type=int, default=5, help="cap on specialists invoked")
    parser.add_argument("--recursion-limit", type=int, default=25, help="graph step backstop")
    parser.add_argument("--persist", action="store_true", help="attach checkpointer + store")
    args = parser.parse_args()

    config = OttoConfig(
        model=args.model,
        max_specialists=args.max_specialists,
        recursion_limit=args.recursion_limit,
        persist=args.persist,
    )

    if args.chat:
        from .chat import chat
        asyncio.run(chat(config))
        return

    if not args.task:
        parser.error("a task is required unless --chat is given")

    result = asyncio.run(run_otto(args.task, config))
    print("specialists:", [h["agent"] for h in result["history"]])
    print("\n" + result["final"])


if __name__ == "__main__":
    main()
