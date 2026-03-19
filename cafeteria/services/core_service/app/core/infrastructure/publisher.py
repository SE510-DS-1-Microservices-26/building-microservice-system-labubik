import asyncio
import json
import logging
import os

import aio_pika

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "core"
ROUTING_KEY = "core-item.created"


async def _publish(event_dict: dict) -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        message = aio_pika.Message(
            body=json.dumps(event_dict, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=ROUTING_KEY)
        logger.info("Published %s event_id=%s", ROUTING_KEY, event_dict.get("event_id"))


def publish_event_sync(event_dict: dict) -> None:
    try:
        asyncio.run(_publish(event_dict))
    except Exception as exc:
        logger.error("Failed to publish event: %s", exc)