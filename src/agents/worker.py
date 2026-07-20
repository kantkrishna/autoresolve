# src/agents/worker.py
import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer

from src.agents.graph import app as agent_app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s : %(message)s"
)
logger = logging.getLogger("worker")


async def consume_alerts():
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic_name = os.getenv("KAFKA_TOPIC", "incidents")
    group_id = os.getenv("KAFKA_GROUP_ID", "autoresolve-ai-swarm")

    consumer = AIOKafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    await consumer.start()
    logger.info(
        f"🟢 AI Worker successfully connected to Kafka. Listening for alerts on topic '{topic_name}'..."  # noqa: E501
    )

    try:
        async for msg in consumer:
            try:
                payload = json.loads(msg.value.decode("utf-8"))

                # Multi-tier identification strategy to completely prevent
                # 'UNKNOWN' threads
                thread_id = "UNKNOWN"
                if isinstance(payload, dict):
                    thread_id = (
                        payload.get("tracking_id")
                        or payload.get("incident_id")
                        or payload.get("alertname")
                        or "UNKNOWN"
                    )
                    # Support nested envelope unpacks
                    if thread_id == "UNKNOWN" and isinstance(
                        payload.get("payload"), dict
                    ):
                        nested = payload["payload"]
                        thread_id = (
                            nested.get("tracking_id")
                            or nested.get("incident_id")
                            or "UNKNOWN"
                        )

                # Check native Kafka record key as last resilient fallback
                if thread_id == "UNKNOWN" and msg.key:
                    try:
                        thread_id = msg.key.decode("utf-8")
                    except Exception:
                        pass

                # Ultimate fallback to broker sequence context coordinates
                if thread_id == "UNKNOWN":
                    thread_id = f"TRK-{msg.partition}-{msg.offset}"

                logger.info(f"🚨 KAFKA ALERT RECEIVED: Processing Incident {thread_id}")
                logger.info(f"🧠 Invoking LangGraph Swarm for {thread_id}...")

                initial_state = {
                    "messages": [],
                    "incident_id": thread_id,
                    "tracking_id": thread_id,
                    "proposed_fix": "",
                }

                thread_config = {"configurable": {"thread_id": thread_id}}

                async for event in agent_app.astream(
                    initial_state, config=thread_config
                ):
                    for node_name, _ in event.items():
                        logger.info(
                            f"💾 Node '{node_name}' finished executing state update sequence."  # noqa: E501
                        )

                logger.info("⏸️  GRAPH PAUSED. Next node in queue: ('execution_node',)")
                logger.info(
                    f"👨‍💻 Waiting for Human-in-the-Loop approval for Thread: {thread_id}"  # noqa: E501
                )

            except Exception as e:
                logger.error(
                    f"❌ Error occurred processing event stream: {str(e)}",
                    exc_info=True,
                )
                continue
    finally:
        await consumer.stop()
        await agent_app.close()


if __name__ == "__main__":
    asyncio.run(consume_alerts())
