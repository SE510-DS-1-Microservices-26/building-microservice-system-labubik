import asyncio
import json
import logging
import os
from datetime import datetime

import aio_pika
from sqlalchemy.orm import sessionmaker

from app.core.application import NotificationService
from app.core.domain import Notification
from app.core.infrastructure.database import engine
from app.core.infrastructure.notification_repository import PostgresNotificationRepository

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "core"
ROUTING_KEY = "core-item.created"
QUEUE_NAME = "notification.core-item.created"


async def process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            body = json.loads(message.body.decode())
            logger.info("Received event_id=%s", body.get("event_id"))

            Session = sessionmaker(bind=engine, autocommit=False)
            with Session() as db:
                repo = PostgresNotificationRepository(db)
                service = NotificationService(repo)

                notification = Notification(
                    event_id=body["event_id"],
                    correlation_id=body.get("correlation_id", ""),
                    core_item_id=body["core_item_id"],
                    owner_user_id=body["owner_user_id"],
                    summary=body.get("summary", ""),
                    payload=body,
                    received_at=datetime.utcnow(),
                )
                service.handle(notification)
        except Exception as exc:
            logger.exception("Error processing message: %s", exc)


async def start_consumer() -> None:
    while True:
        try:
            logger.info("Connecting to RabbitMQ at %s", RABBITMQ_URL)
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)

                exchange = await channel.declare_exchange(
                    EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )

                queue = await channel.declare_queue(QUEUE_NAME, durable=True)
                await queue.bind(exchange, routing_key=ROUTING_KEY)

                logger.info(
                    "Consumer ready — exchange=%s queue=%s routing_key=%s",
                    EXCHANGE_NAME,
                    QUEUE_NAME,
                    ROUTING_KEY,
                )
                await queue.consume(process_message)

                await asyncio.Future()
        except (aio_pika.exceptions.AMQPConnectionError, ConnectionError) as exc:
            logger.warning("RabbitMQ connection lost: %s — retrying in 5s", exc)
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
            return
