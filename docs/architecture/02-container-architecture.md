# AutoResolve Container Architecture Diagram (Level 2)

This diagram maps to the Level 2 Container Diagram established in
Architecture design, now populated with the precise technology
stack selected. It highlights the decoupled, scalable nature of
the deployable units within AutoResolve:
* The independent API Gateway (FastAPI) handling ingestion.
* The Event Streaming backbone (Apache Kafka) ensuring resilient,
  asynchronous hand-offs.
* The AI Orchestration & Reasoning layer, powered by LangGraph and
  Anthropic's Claude 3.5 Sonnet.
* The Persistence Layer distinctly split between transactional
  incident state (PostgreSQL) and semantic runbook search (Qdrant).
* The CI/CD & Operations boundary demonstrating automated deployment
  pipelines (GitHub Actions).

```mermaid
graph TD
    subgraph CI/CD & Operations
        GHA[GitHub Actions]
    end

    subgraph API Gateway
        FA[FastAPI]
    end

    subgraph Event Streaming
        K[Apache Kafka]
    end

    subgraph AI Orchestration & Reasoning
        LG[LangGraph Worker]
        Claude[Anthropic Claude 3.5 Sonnet]
    end

    subgraph Persistence Layer
        PG[(PostgreSQL)]
        QD[(Qdrant Vector DB)]
    end

    %% Data Flow
    Prometheus -->|Webhook| FA
    FA -->|Publish Alert Event| K
    K -->|Consume Event| LG
    LG <-->|Tool Calling / Reasoning| Claude
    LG <-->|ACID Incident State| PG
    LG <-->|Runbook Semantic Search| QD
    GHA -->|Deploy| FA
    GHA -->|Deploy| LG
```