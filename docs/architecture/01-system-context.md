# AutoResolve System Context Diagram (Level 1)

This diagram maps to the C4 modeling approach established the Architecture.
It serves as the high-level Level 1 System Context Diagram, demonstrating
exactly how AutoResolve fits into the broader enterprise ecosystem. It
accurately captures the essential trust boundaries and integration points
defined, including alert ingestion from Prometheus, context gathering from
Kubernetes via MCP, reasoning via the LLM API, and remediation execution
via GitHub.

```mermaid
graph TD
    # Internal Entities
    P[Prometheus / AlertManager]
    AR((AutoResolve System))
    
    # External Entities
    S[Slack / Teams]
    G[GitHub]
    K[Kubernetes Cluster]
    LLM[OpenAI / Anthropic API]

    # Relationships
    P -- "1. Fires Webhook Alert" --> AR
    AR -- "2. Notifies On-Call" --> S
    AR -- "3. Fetches Context & Logs via MCP" --> K
    AR -- "4. Generates Reasoning" --> LLM
    AR -- "5. Opens Remediation PR" --> G
    S -- "6. Approves/Rejects Fix" --> AR
```