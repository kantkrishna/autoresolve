# API Gateway & Security Flow

This diagram illustrates the Phase 4 security posture for the FastAPI Ingestion Gateway, detailing the flow of incoming webhooks through the Rate Limiter and Authentication boundaries before reaching the Kafka Outbox.

```mermaid
sequenceDiagram
    participant P as Prometheus AlertManager
    participant RL as FastAPI (Rate Limiter)
    participant Auth as FastAPI (API Key Auth)
    participant EP as Endpoint (/api/v1/alerts)
    participant K as Kafka Broker

    P->>RL: POST /api/v1/alerts
    alt Rate Limit Exceeded
        RL-->>P: 429 Too Many Requests
    else Within Limits
        RL->>Auth: Pass Request
        alt Invalid API Key
            Auth-->>P: 401 Unauthorized
        else Valid Token
            Auth->>EP: Validate Pydantic Schema
            EP->>K: Produce Event (Fire & Forget)
            EP-->>P: 202 Accepted
        end
    end
```
