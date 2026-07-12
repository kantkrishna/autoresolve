# src/api/producer.py
import json
import logging
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

# We will inject the configuration at runtime
from src.core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Singleton Kafka Producer for asynchronous event queuing."""

    def __init__(self) -> None:
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self.producer.start()
        logger.info("Kafka Producer securely connected to broker.")

    async def stop(self) -> None:
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer connection closed.")

    async def publish_alert(self, topic: str, payload: dict[str, Any]) -> None:
        if not self.producer:
            raise RuntimeError(
                "Kafka Producer is not initialized. Check lifespan hooks."
            )
        await self.producer.send_and_wait(topic, payload)
        logger.info(f"Successfully queued alert to topic: {topic}.")


# Global singleton instance
publisher = EventPublisher()
