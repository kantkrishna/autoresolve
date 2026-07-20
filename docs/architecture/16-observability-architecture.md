# Observability Architecture

To achieve production-readiness, we have implemented a multi-layered observability architecture:
* **Application Edge (FastAPI):** Inject Prometheus middleware to track HTTP request latencies and rate-limit rejections.
* **Distributed Tracing (OTel):** Configure an OpenTelemetry tracer provider that injects trace_id headers into the Kafka producer and extracts them in the LangGraph worker. This correlates the initial webhook alert directly to the final GitHub PR.
* **Agent Telemetry (LangSmith & Prometheus):** Explicitly track LLM token usage and reasoning loop durations using custom Prometheus Histograms and Counters within the get_agnostic_llm execution paths. The LANGCHAIN_TRACING_V2 environment variable natively broadcasts internal state transitions to LangSmith.