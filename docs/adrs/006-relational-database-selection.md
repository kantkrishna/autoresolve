# ADR 006: Relational Database Selection

## Context
The system needs a primary database to store structured incident metadata, LangGraph state checkpoints (time-travel), and audit logs.

## Alternatives Considered
1. **SQLite:** Serverless, file-based relational database.
2. **PostgreSQL:** Advanced, open-source object-relational database.

## Tradeoffs
- SQLite is excellent for local development but struggles with high concurrency. Multiple agents attempting to write state logs simultaneously would trigger file locking errors.
- Postgres is the enterprise gold standard for ACID compliance and handles massive concurrent writes seamlessly.

## Decision
We will use **PostgreSQL**.

## Consequences
- While we use SQLite for local OpenSmith tracing, the core application state and LangGraph MemorySaver will rely on Postgres for production deployments.
