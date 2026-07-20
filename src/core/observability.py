# src/core/observability.py
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from prometheus_client import Counter, Histogram

# --- OpenTelemetry Configuration ---
resource = Resource.create({"service.name": "autoresolve-engine"})
provider = TracerProvider(resource=resource)
# For production, replace ConsoleSpanExporter with OTLPSpanExporter
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# --- Prometheus Metrics Registry ---
# We attach to the default REGISTRY to easily expose via ASGI app

ALERT_INGESTION_COUNTER = Counter(
    "autoresolve_alerts_ingested_total",
    "Total number of alerts ingested via webhook",
    ["source", "status"],
)

AGENT_PROCESSING_TIME = Histogram(
    "autoresolve_agent_processing_seconds",
    "Time spent executing an agentic reasoning loop",
    ["agent_name"],
)

LLM_TOKEN_USAGE = Counter(
    "autoresolve_llm_tokens_total",
    "Total tokens consumed by LLM calls",
    ["model", "token_type"],  # token_type: input, output
)
