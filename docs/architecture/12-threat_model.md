```markdown
# Enterprise Threat Model (STRIDE)

| Threat Type | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Spoofing** | Forged Prometheus alerts triggering AI compute drain. | Phase 4 API Key / HMAC validation on FastAPI. |
| **Tampering** | Prompt injection attacks hiding in log payloads. | Strict Pydantic parsing and output schema enforcement. |
| **Repudiation** | AI modifies infrastructure without accountability. | LangGraph checkpointer (MemorySaver) and HITL Review Node. |
| **Information Disclosure** | LLM leaks sensitive cluster secrets. | Secrets are never passed to the LLM; they remain trapped inside the MCP Servers. |
| **Denial of Service** | Alert storm overwhelms the LLM API rate limits. | Kafka buffering + Fire-and-Forget API pattern. |
| **Elevation of Privilege** | AI agent attempts unauthorized cluster deletion. | Principle of Least Privilege: K8s MCP Server is scoped to `Read-Only` roles. |