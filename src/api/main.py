# src/api/main.py
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, status

from src.api.auth import verify_api_key
from src.api.producer import publisher
from src.api.rate_limit import RateLimiter
from src.api.schemas import PrometheusAlert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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


@app.post(
    "/webhook/prometheus",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[
        Depends(verify_api_key),
        Depends(RateLimiter(requests_per_minute=100)),
    ],
)
async def ingest_alert(alert: PrometheusAlert) -> dict[str, Any]:
    """Ingest alerts, validate against prompt injection, and queue to Kafka."""
    try:
        # Extract the computed deterministic hash
        incident_id = alert.tracking_id

        # Publish with the partition key
        await publisher.publish_alert(
            topic="incidents", payload=alert.model_dump(), key=incident_id
        )

        # Return observability trace to the caller
        return {
            "status": "accepted",
            "tracking_id": incident_id,
            "message": "Alert safely queued for autonomous AI triage.",
        }
    except Exception as e:
        logger.error(f"Broker failure during alert publishing: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event broker unavailable. AI degraded; routing to human fallback.",
        )
