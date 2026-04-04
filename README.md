# Cafeteria - Practice 6

## Architecture

```
Client (curl)
      │
      ▼
Gateway (:8080)  ── generates X-Correlation-Id
      │          │
      ▼          ▼
Core Service    Users Service
  (:8081)         (:8082)
   │  ── GET /users/{id} ──▶  │
   │                          ▼
   │                       Users DB
   │
   ├──▶ Core DB
   │
   └──▶ RabbitMQ (:5672) ──▶ Notification Service (:8083) ──▶ Notification DB
         (exchange: core)      (queue: notification.core-item.created)
```

## Event Contract

**Event name:** `core-item.created`

**Exchange:** `core`

**Queue:** `notification.core-item.created`

**Routing key:** `core-item.created`

### Payload example

```json
{
  "event_id": "038f908a-98d4-44f4-97e8-63f09c0b3641",
  "occurred_at": "2026-03-23T23:31:51.893714+00:00",
  "correlation_id": "4ced0063-cfe1-4c03-86a8-852c29b0b753",
  "core_item_id": "009dc1f0-4c92-489a-ad92-30b279b7658d",
  "owner_user_id": "f6473927-31eb-4067-85a7-449532c12e98",
  "summary": "Order 'Latte' x2 by Anna"
}
```

## Idempotency

The Notification Service ensures **no duplicate notifications** are stored:

- The `notifications` table has `event_id` as a **primary key**
- On duplicate `event_id`, the `IntegrityError` is caught and the message is silently ignored

## How to run

```bash
docker compose up --build
```

This starts 8 containers: `rabbitmq`, `core-db`, `users-db`, `notification-db`, `core-service`, `users-service`, `notification-service`, `gateway`.

To stop:

```bash
docker compose down
```

## Service URLs

| Service              | Direct access          | Via Gateway                  |
|----------------------|------------------------|------------------------------|
| Gateway              | http://localhost:8080   | —                            |
| Core Service         | http://localhost:8081   | http://localhost:8080/core/   |
| Users Service        | http://localhost:8082   | http://localhost:8080/users/  |
| Notification Service | http://localhost:8083   | —                            |
| RabbitMQ Management  | http://localhost:15672  | — (login: guest / guest)     |

## How to verify

### 1. Check RabbitMQ is running

Open http://localhost:15672 (login: `guest` / `guest`).

- Go to **Exchanges** tab — verify `core` exchange exists
- Go to **Queues** tab — verify `notification.core-item.created` queue exists

### 2. Create a user

```bash
curl -X POST http://localhost:8082/users \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Anna"}'
```

```json
{"id": "f6473927-31eb-4067-85a7-449532c12e98", "display_name": "Anna"}
```

### 3. Create an order (triggers the event)

```bash
curl -X POST http://localhost:8081/core-items \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Anna",
    "item_name": "Latte",
    "quantity": 2,
    "price": 5.0,
    "owner_user_id": "f6473927-31eb-4067-85a7-449532c12e98"
  }'
```

### 4. Check notifications were stored

```bash
curl http://localhost:8083/notifications
```

Should return a JSON list with the stored notification.

### 5. Verify directly in the database

```bash
docker compose exec notification-db psql -U postgres -d notification_db \
  -c "SELECT event_id, summary, received_at FROM notifications;"
```

Expected output:

```
               event_id               |          summary          |        received_at
--------------------------------------+---------------------------+----------------------------
 038f908a-98d4-44f4-97e8-63f09c0b3641 | Order 'Latte' x2 by Anna | 2026-03-23 23:31:51.929547
```

## Responsibility split

- **Kseniia Hanziuk:** Event contract, publisher, event publishing in Core Service
- **Sofiia Churikova:** Notification Service
