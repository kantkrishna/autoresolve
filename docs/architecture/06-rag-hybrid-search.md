```mermaid
graph TD
    Query[Incident Alert: OOMKilled] --> Dense[FastEmbed Dense Vector]
    Query --> Sparse[FastEmbed BM25 Sparse Vector]
    
    Dense --> DB[(Qdrant Collection)]
    Sparse --> DB
    
    DB -->|Reciprocal Rank Fusion| Result[Top Runbook Retrieved]
    Result --> ResolutionAgent[Resolution Agent Prompts Fix]
```