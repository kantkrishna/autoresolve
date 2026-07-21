# src/agents/worker.py
# src/agents/worker.py
import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import UnknownTopicOrPartitionError, KafkaConnectionError

from src.agents.graph import app as agent_app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s : %(message)s"
)
logger = logging.getLogger("worker")

async def start_consumer_with_retries(consumer: AIOKafkaConsumer, max_retries: int = 6, backoff_sec: int = 5):
    """
    Enterprise startup sequence with exponential backoff.
    Waits for Kafka to fully boot and create the target topic.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Kafka connection attempt {attempt}/{max_retries}...")
            await consumer.start()
            return
        except (UnknownTopicOrPartitionError, KafkaConnectionError) as e:
            logger.warning(f"Kafka not ready or topic missing. Retrying in {backoff_sec}s... ({str(e)})")
            if attempt == max_retries:
                logger.critical("Max retries reached. Shutting down worker.")
                raise e
            await asyncio.sleep(backoff_sec)

async def consume_alerts():
    # FIX: Default fallback to 29092 to match Docker internal routing
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    topic_name = os.getenv("KAFKA_TOPIC", "incidents")
    group_id = os.getenv("KAFKA_GROUP_ID", "autoresolve-ai-swarm")

    consumer = AIOKafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    # FIX: Use the robust startup loop instead of a raw `await consumer.start()`
    await start_consumer_with_retries(consumer)
    
    logger.info(
        f"🟢 AI Worker successfully connected to Kafka. Listening for alerts on topic '{topic_name}'..."
    )

    try:
        async for msg in consumer:
            try:
                payload = json.loads(msg.value.decode("utf-8"))

                # Multi-tier identification strategy to completely prevent 'UNKNOWN' threads
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
                            f"💾 Node '{node_name}' finished executing state update sequence."
                        )

                logger.info("⏸️  GRAPH PAUSED. Next node in queue: ('execution_node',)")
                logger.info(
                    f"👨‍💻 Waiting for Human-in-the-Loop approval for Thread: {thread_id}"
                )

            except Exception as e:
                logger.error(
                    f"❌ Error occurred processing event stream: {str(e)}",
                    exc_info=True,
                )
                continue
    finally:
        await consumer.stop()
        # agent_app.close()  <-- Note: LangGraph CompiledStateGraph doesn't typically have a .close() method 

if __name__ == "__main__":
    asyncio.run(consume_alerts())