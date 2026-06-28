# otto-langgraph

Claude Agent SDK inside LangGraph nodes. LangGraph owns the graph, each node runs
a full Claude agent.

## The idea

Two layers that do different jobs:

- **LangGraph** decides what runs when: state, edges, conditional routing, parallel work.
- **Claude Agent SDK** runs each step as a full agent, with its own system prompt and tools.

Each node in the graph is a Python function that calls the SDK. Results flow back into
graph state. Conditional edges branch on that state.

Baseline for the graph is Otto, a router-plus-specialists orchestrator. Otto classifies a
task, picks one specialist, runs it, then sends the result through an adversarial review gate.

## Otto maps onto the graph

| Otto | LangGraph port |
|------|----------------|
| Router (classify task, pick a unit) | Router node, then a conditional edge |
| Specialists (o7, rock, ...) | One node each, a Claude SDK call with that system prompt |
| Verify gate (devil review) | Review node before END, loops back on a revise verdict |
| Escalation rules | Conditional edges that read state |

## Learning ladder

Built one rung at a time:

1. One Claude Agent SDK call, standalone. See the message stream. (`rung1.py`)
2. Wrap the call in one LangGraph node. Watch state flow in and out.
3. Add a second node and an edge.
4. Add the router and a conditional edge.
5. Add the verify gate and loop-back. Mini-Otto.

## Run

```bash
pip install -r requirements.txt
npm i -g @anthropic-ai/claude-code
export ANTHROPIC_API_KEY=sk-ant-...
python rung1.py
```

## Credit

Integration pattern from Khaled Elfakharany,
[Claude Agent SDK inside LangGraph nodes](https://www.khaledelfakharany.com/articles/langgraph-claude-sdk-integration).
