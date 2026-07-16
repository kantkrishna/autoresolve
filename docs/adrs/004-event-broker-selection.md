# ADR 004: Event Broker Selection

## Context
Prometheus Alertmanager can generate massive "alert storms" during cascading failures. AutoResolve needs an event bus to decouple the fast API ingestion from the slower AI reasoning loop.

## Alternatives Considered
1. **Redis (via Celery/RQ):** In-memory data store and message broker.
2. **Apache Kafka:** Distributed, durable commit log.

## Tradeoffs
- Redis is simpler to deploy, but it stores data in memory by default. If the AutoResolve gateway crashes during a massive incident, active alert tasks could be permanently lost.
- Kafka persists messages to disk as an append-only log, guaranteeing at-least-once delivery even in catastrophic failure scenarios.

## Decision
We will use **Apache Kafka**.

## Consequences
- Introduces operational complexity and higher JVM memory overhead.
- Guarantees 100% durable incident task queuing, an absolute necessity for Tier-1 SRE tooling.
