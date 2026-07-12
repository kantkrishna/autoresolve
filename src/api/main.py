# src/api/main.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status

from src.api.producer import publisher
from src.api.schemas import PrometheusAlert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages global connections tied to the API lifecycle."""
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


@app.post("/webhook/prometheus", status_code=status.HTTP_202_ACCEPTED)
async def ingest_alert(alert: PrometheusAlert) -> dict[str, str]:
    """
    Ingest alerts, validate against prompt injection, and queue to Kafka.
    """
    try:
        # Convert the Pydantic model to a dictionary and queue it
        await publisher.publish_alert("incidents", alert.model_dump())
        return {
            "status": "accepted",
            "message": "Alert queued for autonomous AI triage.",
        }
    except Exception as e:
        logger.error(f"Broker failure during alert publishing: {e}")
        # Return 503 so Alertmanager knows to trigger the human fallback channel
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event broker unavailable. AI degraded; routing to human fallback.",
        )
