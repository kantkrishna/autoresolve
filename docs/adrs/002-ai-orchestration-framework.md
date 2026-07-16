# ADR 002: AI Orchestration Framework Selection

## Context
AutoResolve requires an orchestration framework to govern the reasoning loop of multiple AI agents (Triage, Investigation, Resolution) responding to production incidents.

## Alternatives Considered
1. **AutoGen:** Highly capable conversational multi-agent framework.
2. **CrewAI:** Task-based framework focusing on sequential agent delegation.
3. **LangGraph:** Graph-based state machine orchestrator built on LangChain.

## Tradeoffs
- AutoGen relies on unstructured LLM-to-LLM dialogue, which is highly non-deterministic and prone to infinite loops in production SRE scenarios.
- CrewAI is excellent for sequential tasks but abstracts away too much control over low-level state transitions.
- LangGraph models workflows as explicit state machines with cyclical edges and typed memory reducers.

## Decision
We will use **LangGraph**.

## Consequences
- Requires defining explicit nodes and conditional routing edges.
- Provides the strict determinism, debuggability, and MemorySaver checkpointing required for Human-in-the-Loop (HITL) incident response.
