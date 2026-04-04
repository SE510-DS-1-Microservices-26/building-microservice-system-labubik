import asyncio
import json
import logging
import os

import aio_pika

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "core"
ROUTING_KEY = "core-item.created"


def build_rabbitmq_url() -> str:
    explicit_url = os.getenv("RABBITMQ_URL")
    if explicit_url:
        return explicit_url

    host = os.getenv("RABBITMQ_HOST", "localhost")
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return f"amqp://{user}:{password}@{host}:5672/"


RABBITMQ_URL = build_rabbitmq_url()


async def _publish(event_dict: dict, correlation_id: str = "") -> None:
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
            headers={"correlation_id": correlation_id},
        )
        await exchange.publish(message, routing_key=ROUTING_KEY)
        logger.info(
            "Published %s event_id=%s correlation_id=%s",
            ROUTING_KEY,
            event_dict.get("event_id"),
            correlation_id,
        )


def publish_event_sync(event_dict: dict, correlation_id: str = "") -> None:
    try:
        asyncio.run(_publish(event_dict, correlation_id=correlation_id))
    except Exception as exc:
        logger.error("Failed to publish event: %s", exc)