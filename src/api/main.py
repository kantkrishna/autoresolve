# src/api/main.py
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from opentelemetry import trace
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Correctly referencing our Phase 5 modules
from src.api.auth import verify_api_key
from src.api.producer import publisher
from src.api.rate_limit import RateLimiter
from src.api.schemas import PrometheusAlert

# Phase 13 Observability imports
from src.core.observability import ALERT_INGESTION_COUNTER, tracer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the startup and shutdown lifecycle of the FastAPI app."""
    try:
        await publisher.start()
    except Exception as e:
        logger.error(f"FATAL: Failed to start Kafka Producer: {e}")
    yield
    await publisher.stop()


app = FastAPI(
    title="AutoResolve API Gateway",
    description="Enterprise webhook gateway for intercepting Prometheus alerts.",
    version="1.0.0",
    lifespan=lifespan,
)

try:
    from src.production.prod_resilience import SystemHealthManager
except ImportError:
    from src.production.prod_resilience import SystemHealthManager

# Initialize the health manager globally
health_manager = SystemHealthManager()

async def check_database() -> bool:
    """Real-time ping to Postgres state database."""
    # Example: return await db_pool.ping()
    return True

async def check_mcp_servers() -> bool:
    """Real-time ping to MCP multiplexer."""
    # Example: return await mcp_client.is_connected()
    return True

# Register dependencies before application starts taking traffic
health_manager.register_dependency("postgres_state", check_database)
health_manager.register_dependency("mcp_servers", check_mcp_servers)

@app.get("/health/ready", tags=["Observability"])
async def readiness_probe():
    """
    Kubernetes Readiness Probe.
    Kubelet calls this periodically. If it returns a 503, the pod is pulled 
    from the service load balancer until dependencies recover.
    """
    status = await health_manager.check_readiness()
    if status["status"] != "ok":
        # 503 Service Unavailable signals to K8s that we cannot process alerts
        raise HTTPException(status_code=503, detail=status)
    return status

@app.get("/metrics", include_in_schema=False)
async def get_metrics() -> Response:
    """Exposes native Prometheus metrics for scraping."""
    return Response(
        content=generate_latest(), 
        media_type=CONTENT_TYPE_LATEST
    )


@app.post(
    "/webhook/prometheus",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[
        Depends(verify_api_key),
        Depends(RateLimiter(requests_per_minute=100)),
    ],
)
async def ingest_alert(alert: PrometheusAlert, request: Request) -> dict[str, Any]:
    """
    Ingests an alert from Prometheus, records observability metrics, 
    and publishes to the Kafka event bus.
    """
    with tracer.start_as_current_span("ingest_alert_webhook") as span:
        
        # Dynamically extract attributes from the flattened Pydantic model safely
        alert_name = getattr(alert, "alertname", "unknown")
        span.set_attribute("alert.name", alert_name)
        span.set_attribute("alert.status", getattr(alert, "status", "unknown"))
        
        try:
            incident_id = alert.tracking_id if alert.tracking_id else str(uuid.uuid4())
            
            # Publish with the partition key
            await publisher.publish_alert(
                topic="incidents", payload=alert.model_dump(), key=incident_id
            )
            
            span.set_attribute("event_bus.incident_id", incident_id)
            
            # Update Success Metrics
            ALERT_INGESTION_COUNTER.labels(
                source="prometheus", 
                status="success"
            ).inc()
            
            return {
                "status": "accepted",
                "tracking_id": incident_id,
                "message": "Alert safely queued for autonomous AI triage.",
            }
            
        except Exception as e:
            # Update Failure Metrics & Trace Exception
            ALERT_INGESTION_COUNTER.labels(
                source="prometheus", 
                status="error"
            ).inc()
            
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            logger.error(f"Broker failure during alert publishing: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Event broker unavailable. AI degraded; routing to human fallback.",
            )
