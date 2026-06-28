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

Built one rung at a time, each rung adds one concept. All rungs live in `learning/`.

Done:

1. One Claude Agent SDK call, standalone. See the message stream. (`learning/rung1.py`)
2. Wrap the call in one LangGraph node. State flows in and out. (`learning/rung2.py`)
3. Two nodes and an edge. Second node reads what the first wrote. (`learning/rung3.py`)
4. Router plus a conditional edge. The graph picks a specialist. (`learning/rung4.py`)
5. Verify gate and bounded loop-back. Mini-Otto. (`learning/rung5.py`)

Ahead, one primitive per rung, toward the full framework:

6. Parallel fan-out. Run a squad of specialists at once.
7. Reducers. `Annotated[list, add]` merges parallel results without clobber.
8. Structured output. Agents return typed Pydantic objects, no string sniffing.
9. Streaming. `astream` and its modes: values, updates, messages.
10. Persistence. A checkpointer plus `thread_id` survives a stop mid-graph.
11. Human-in-the-loop. `interrupt` pauses for input, `Command(resume=...)` continues.
12. Subgraphs. A whole graph runs as one node in a parent graph.
13. Dynamic fan-out. `Send` spawns N workers from a runtime list (map-reduce).
14. Long-term memory. A store holds facts across threads, not just one run.
15. Time travel. Inspect state history, edit a past step, replay from there.
16. Capstone. Supervisor pattern, retry policy, config. The full Otto.

## Two cages, two stops

Every loop has a smart stop and a dumb backstop, at two scales:

| Layer | Smart stop | Dumb backstop |
|-------|-----------|---------------|
| Inside a node (SDK) | model emits `end_turn` | `max_turns` |
| Across the graph (LangGraph) | verdict or revision cap | `recursion_limit` |

## Run

```bash
pip install -r requirements.txt
npm i -g @anthropic-ai/claude-code
export ANTHROPIC_API_KEY=sk-ant-...
python learning/rung1.py
```

## otto/ (the production package)

The 16 rungs teach the primitives. `otto/` composes them into one orchestrator.

```bash
pip install -e .
otto "Make our 8-second drone reconnect faster and safer"
otto "Audit this camera pipeline for leaks" --max-specialists 4 --persist
```

Or from Python:

```python
import asyncio
from otto import run_otto, OttoConfig

result = asyncio.run(run_otto("Profile the render loop", OttoConfig(max_specialists=4)))
print(result["final"])
```

### Architecture

```
START -> supervisor --pick--> specialist -> supervisor (loop) --done--> finalize -> END
```

- **Supervisor loop** picks the next specialist each turn from the roster, or stops.
- **Roster** is 11 specialists, one system prompt each (`roster.py`).
- **Structured routing**: the supervisor returns a validated `Decision`, no string sniffing.
- **Reducer**: every specialist appends to one shared `history` list.
- **Retry**: each specialist node carries a `RetryPolicy` for transient failures.
- **Config**: `OttoConfig` tunes model, caps, retries, persistence.
- **Bounded** by three stops: supervisor `done`, `max_specialists` cap, `recursion_limit`.

| Module | Holds |
|--------|-------|
| `config.py` | `OttoConfig` |
| `sdk.py` | `run_agent`, `run_structured` (tool-free Claude calls) |
| `roster.py` | the specialist system prompts |
| `schemas.py` | the `Decision` contract |
| `graph.py` | `build_otto`, the StateGraph |
| `__main__.py` | the `otto` CLI |

### What it is and is not

It is a working orchestrator that composes every rung: routing, loops,
reducers, structured output, retry, persistence, dynamic control flow. It runs
on your Claude login or an `ANTHROPIC_API_KEY`.

For real production you would still add durable checkpoint and store backends
(Postgres over the in-memory ones), tracing and metrics, an eval harness, and
rate-limit handling. The graph is the hard part and it is here. Those are
operational layers around it.

```bash
pytest          # structural tests: build, routing, roster
```

## Credit

Integration pattern from Khaled Elfakharany,
[Claude Agent SDK inside LangGraph nodes](https://www.khaledelfakharany.com/articles/langgraph-claude-sdk-integration).
