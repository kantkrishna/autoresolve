# ADR 007: Foundation Model Provider

## Context
AutoResolve requires a highly capable Large Language Model (LLM) to perform complex reasoning, structural JSON output, and tool calling via the Model Context Protocol (MCP).

## Alternatives Considered
1. **OpenAI (GPT-4o):** Industry-leading model with strong reasoning capabilities.
2. **Anthropic (Claude 3.5 Sonnet):** The pioneer of the MCP standard, highly tuned for coding and tool use.

## Tradeoffs
- Hardcoding either provider creates vendor lock-in and prevents users with strict data privacy requirements from running local models.
- Claude 3.5 Sonnet has demonstrated superior adherence to system prompts and complex tool definitions in DevSecOps contexts.

## Decision
We will set **Anthropic (Claude 3.5 Sonnet)** as the recommended cloud provider, but architect the system using **LiteLLM** to remain provider-agnostic.

## Consequences
- AutoResolve natively supports Anthropic, OpenAI, and Local LLMs (Ollama) by routing all requests through the LiteLLM proxy, fulfilling the requirement for air-gapped execution.
