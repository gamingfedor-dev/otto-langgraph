LangGraph and the Claude Agent SDK keep getting described as some new kind of magic.

I rebuilt my own multi-agent setup in both. They are not magic, and that is the good news.

The push to actually try it came from Khaled Elfakharany. His write-up on running the Claude Agent SDK inside LangGraph nodes is what made it click: the graph owns the control flow, and each node is a full Claude agent.

So I tested it against what I already had. I run a config-driven agent orchestrator inside Claude Code. A router picks a specialist, the specialist works, an adversarial reviewer gates the result.

The frameworks did not hand me new ideas. They named the ones I use every day: routing, state, retries, fan-out.

I learned LangGraph the slow way anyway. Sixteen tiny steps, one concept each, from a single SDK call up to a supervisor that loops over 11 specialists. Then I composed them into a working package with structured routing, retries, optional persistence, and a chat mode that remembers across turns.

What it is: a working orchestrator that runs on your Claude login.
What it is not: production infrastructure. No durable backends or tracing yet. The graph is the hard part, and that part is done.

The lesson stuck. The frameworks are thin. The hard parts are good prompts, clean state, and sane routing, and those move with you between any of them.

If you keep avoiding one of these tools because it looks like a wall of new concepts, it probably is not. Which one are you putting off?

#LangGraph #AIAgents #ClaudeAI
