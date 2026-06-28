I almost skipped LangGraph. It looked like hype with a fresh vocabulary.

Khaled Elfakharany changed my mind. His write-up on running the Claude Agent SDK inside LangGraph nodes made it click: the graph owns control flow, each node is a full Claude agent.

So I tested it against what I already run. An agent orchestrator inside Claude Code. A router picks a specialist. A reviewer gates the result.

Then I saw it.

LangGraph did not teach me new ideas. It named the ones I already use by instinct.

Routing. State. Reducers. Retries. Fan-out. Persistence. Memory. Human-in-the-loop.

Every one a move I already reach for. The framework just handed them a vocabulary and a graph.

The tool is thin. The judgment is everything.

Good prompts. Clean state. Sane routing. Those travel with you, whichever framework is in fashion this quarter.

So I built the thing: a supervisor that loops over 11 specialists, structured routing, retries, persistence, a chat mode that remembers across turns. Runs on a Claude login.

If a tool looks like a wall of new concepts, look closer. It is usually familiar ground wearing new names.

Which one have you been putting off?

#LangGraph #AIAgents #ClaudeAI
