I spent a few evenings rebuilding my own multi-agent setup in LangGraph, one primitive at a time. The spark came from Khaled Elfakharany, whose write-up on running the Claude Agent SDK inside LangGraph nodes made the whole thing click. Credit where it is due.

Background. I run a config-driven agent orchestrator inside Claude Code. A router picks a specialist, the specialist does the work, an adversarial reviewer gates the result. I kept hearing LangGraph and the Claude Agent SDK called some new kind of magic. They are not. They name concepts I already use every day: orchestration, state, deterministic routing, retries.

Khaled's pattern gave me the missing piece: each LangGraph node is a full Claude agent, the graph owns control flow, the SDK owns execution. So I tested it. I ported my orchestrator and learned the framework by climbing 16 small rungs, each adding one concept:

- one Claude Agent SDK call
- wrap it in a graph node
- routing, loops, parallel fan-out
- reducers, structured output, streaming
- persistence, human-in-the-loop
- subgraphs, dynamic fan-out with Send
- long-term memory, time travel
- a supervisor capstone

Then I composed the rungs into a standalone package: an 11-specialist orchestrator with structured routing, per-node retry, optional persistence, a CLI, and a conversational mode that remembers across turns.

What it is: a working orchestrator that runs on your Claude login.
What it is not: production infrastructure. No durable backends, tracing, or eval harness yet. The graph is the hard part and it is done. The rest is operational layers around it.

The lesson held. The frameworks are thin. The hard parts are good prompts, sane routing, and clean state, and those transfer between any of them.

Thanks Khaled for the idea. Repo and the original article in the comments.

#LangGraph #AIAgents #ClaudeAI #LLM
