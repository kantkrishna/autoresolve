# Failure Scenarios & Recovery Strategies

1. **LLM Provider Outage (e.g., OpenAI down):**
   * *Recovery:* `LiteLLM` router automatically falls back to Anthropic Claude 3.5 or Local Ollama instance.
2. **Alert Storm (Massive K8s node failure):**
   * *Recovery:* FastAPI queues messages into Kafka without blocking. Consumer scales horizontally to process the backlog.
3. **Graph Execution Crash (Network Timeout during tool call):**
   * *Recovery:* LangGraph `MemorySaver` retains the state. Worker simply restarts the graph from the last successful node execution.