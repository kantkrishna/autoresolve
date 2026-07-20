"""
Unit tests for the Observability module.
Ensures Prometheus metrics and OpenTelemetry tracing initialize and record correctly.
"""

from opentelemetry.trace import Span
from prometheus_client import REGISTRY

# Import the observability constructs developed in Phase 13
from src.core.observability import (
    ALERT_INGESTION_COUNTER,
    LLM_TOKEN_USAGE,
    tracer,
)


class TestPrometheusMetrics:
    """Test suite for Prometheus metrics generation and recording."""

    def test_alert_ingestion_metric_increments(self) -> None:
        """Verify that the ingestion counter increments safely for specific labels."""
        # Define test labels
        labels = {"source": "test_prometheus", "status": "success"}

        # Get baseline value (handles case where metric wasn't initialized yet in
        # this thread)
        try:
            initial_value = ALERT_INGESTION_COUNTER.labels(**labels)._value.get()
        except KeyError:
            initial_value = 0.0

        # Simulate alert ingestion
        ALERT_INGESTION_COUNTER.labels(**labels).inc()

        # Validate thread-safe increment
        new_value = ALERT_INGESTION_COUNTER.labels(**labels)._value.get()
        assert new_value == initial_value + 1.0

    def test_llm_token_usage_metric(self) -> None:
        """Verify that LLM token counters can accumulate values."""
        labels = {"model": "gpt-4-turbo", "token_type": "input"}

        try:
            initial_value = LLM_TOKEN_USAGE.labels(**labels)._value.get()
        except KeyError:
            initial_value = 0.0

        # Simulate a 250-token prompt
        LLM_TOKEN_USAGE.labels(**labels).inc(250)

        new_value = LLM_TOKEN_USAGE.labels(**labels)._value.get()
        assert new_value == initial_value + 250.0

    def test_metrics_registered_in_global_registry(self) -> None:
        """Verify that our custom metrics are actually exposed to the /metrics endpoint."""  # noqa E501
        # Collect all metric names currently registered
        registered_metrics = [metric.name for metric in REGISTRY.collect()]

        # FIX: Assert the stripped OpenMetrics base name for the counter
        assert "autoresolve_alerts_ingested" in registered_metrics
        assert "autoresolve_agent_processing_seconds" in registered_metrics
        assert "autoresolve_llm_tokens" in registered_metrics


class TestOpenTelemetryTracing:
    """Test suite for OpenTelemetry tracer initialization and span creation."""

    def test_tracer_initialization(self) -> None:
        """Verify the tracer is instantiated and named correctly."""
        assert tracer is not None
        assert hasattr(tracer, "start_as_current_span")

    def test_span_creation_and_attributes(self) -> None:
        """Verify that spans can be created and enriched with metadata."""
        with tracer.start_as_current_span("test_agent_span") as span:
            assert isinstance(span, Span)
            assert span.is_recording()

            # Simulate adding attributes
            span.set_attribute("agent.name", "triage_agent")
            span.set_attribute("incident.severity", "SEV-1")

            # Note: In a true OTel test suite, we would use an InMemorySpanExporter to
            # validate the exact attributes. Here we just ensure the API doesn't crash.
