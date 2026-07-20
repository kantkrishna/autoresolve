# src/api/producer.py
import json
import logging
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

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

    # REFACTORED: Now requires a partition key
    # async def publish_alert(
    #     self, topic: str, payload: dict[str, Any], key: str
    # ) -> None:
    #     if not self.producer:
    #         raise RuntimeError("Kafka Producer is not initialized.")

    #     # The key guarantees alerts for the same service are processed sequentially
    #     await self.producer.send_and_wait(topic, value=payload, key=key.encode("utf-8"))
    #     logger.info(f"Successfully queued alert to {topic} with Tracking ID: {key[:8]}")
    async def publish_alert(self, topic: str, payload: dict, key: str | None = None) -> None:
        """Publishes a JSON payload to a specific Kafka topic."""
        if not self.producer:
            raise RuntimeError("Producer not initialized. Call start() first.")
        
        # Safely handle None keys
        encoded_key = key.encode("utf-8") if key else None
        
        # FIX: Pass the raw dictionary ('payload'). 
        # The AIOKafkaProducer's built-in value_serializer handles the JSON/byte encoding.
        await self.producer.send_and_wait(
            topic, 
            value=payload, 
            key=encoded_key
        )


publisher = EventPublisher()
