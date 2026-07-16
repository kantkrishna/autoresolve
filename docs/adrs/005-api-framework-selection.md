# ADR 005: API Framework Selection

## Context
AutoResolve requires an API gateway to ingest incoming webhooks from Prometheus Alertmanager and route them to the event broker.

## Alternatives Considered
1. **Flask:** Traditional, synchronous WSGI web framework.
2. **FastAPI:** Modern, fast, asynchronous ASGI web framework.

## Tradeoffs
- AI API calls and Kafka producer connections are heavily asynchronous (I/O bound). Flask's synchronous nature would block threads under heavy load.
- FastAPI is natively asynchronous, generates OpenAPI documentation automatically, and enforces strict Pydantic data validation natively.

## Decision
We will use **FastAPI**.

## Consequences
- Alert payloads are automatically validated against Pydantic schemas, preventing malformed alerts or prompt injection vectors from reaching the AI layer.
