# Cafeteria - Practice 5

## Core Item

**Order** — the main aggregate of the system. Represents a cafeteria order with fields: `id`, `customer_name`, `item_name`, `quantity`, `price`, `total`, `status`, `owner_user_id`.

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
   ▼                          ▼
Core DB                    Users DB
```

| Component     | Responsibility                                             |
|---------------|------------------------------------------------------------|
| Gateway       | Routes requests to Core and Users; adds `X-Correlation-Id` |
| Core Service  | Owns Order (Core Item) and business rules                  |
| Users Service | Owns user/profile data                                     |
| Core DB       | PostgreSQL database for Core Service only                  |
| Users DB      | PostgreSQL database for Users Service only                 |

### Data ownership rules

- Core Service does **not** write to Users DB
- Users Service does **not** write to Core DB
- Services communicate only via HTTP

## How to run
```bash
docker compose up --build
```

This starts 5 containers: `core-db`, `users-db`, `core-service`, `users-service`, `gateway`.

Wait until all services are healthy.

To stop:
```bash
docker compose down
```

## Service URLs

| Service        | Direct access          | Via Gateway                  |
|----------------|------------------------|------------------------------|
| Gateway        | http://localhost:8080   | —                            |
| Core Service   | http://localhost:8081   | http://localhost:8080/core/   |
| Users Service  | http://localhost:8082   | http://localhost:8080/users/  |

## API Endpoints

### Users Service

| Method | Endpoint        | Description       |
|--------|-----------------|-------------------|
| POST   | `/users`        | Create a user     |
| GET    | `/users/{id}`   | Get user by ID    |
| GET    | `/health`       | Health check      |

### Core Service

| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| POST   | `/core-items`                 | Create an order          |
| GET    | `/core-items/{id}`            | Get order by ID          |
| PATCH  | `/core-items/{id}/status`     | Update order status      |
| GET    | `/health`                     | Health check             |

### Gateway Routes

| Path prefix | Routed to     |
|-------------|---------------|
| `/core/*`   | Core Service  |
| `/users/*`  | Users Service |

## Example curl commands

All requests go through the Gateway at `http://localhost:8080`.

### 1. Health check
```bash
curl http://localhost:8080/health
```
```json
{"status": "ok", "service": "gateway"}
```

### 2. Create a user
```bash
curl -X POST http://localhost:8080/users/ \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Anna"}'
```
```json
{"id": "259c0118-153b-48df-a76f-20cdd6b9a074", "display_name": "Anna"}
```

### 3. Get a user
```bash
curl http://localhost:8080/users/259c0118-153b-48df-a76f-20cdd6b9a074
```
```json
{"id": "259c0118-153b-48df-a76f-20cdd6b9a074", "display_name": "Anna"}
```

### 4. Create an order for an existing user (success)
```bash
curl -X POST http://localhost:8080/core/core-items \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Anna",
    "item_name": "Salad",
    "quantity": 1,
    "price": 150.50,
    "owner_user_id": "259c0118-153b-48df-a76f-20cdd6b9a074"
  }'
```
```json
{
  "id": "96c600fa-bc34-4d11-884a-4ca920495546",
  "customer_name": "Anna",
  "item_name": "Salad",
  "quantity": 1,
  "price": 150.5,
  "total": 150.5,
  "status": "created",
  "owner_user_id": "259c0118-153b-48df-a76f-20cdd6b9a074"
}
```

### 5. Create an order for a non-existing user (fails with 400)
```bash
curl -X POST http://localhost:8080/core/core-items \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Labuba",
    "item_name": "Pizza",
    "quantity": 1,
    "price": 200.0,
    "owner_user_id": "00000000-0000-0000-0000-000000000000"
  }'
```
```json
{"detail": "User 00000000-0000-0000-0000-000000000000 does not exist"}
```

### 6. Get an order
```bash
curl http://localhost:8080/core/core-items/96c600fa-bc34-4d11-884a-4ca920495546
```

### 7. Update order status
```bash
curl -X PATCH http://localhost:8080/core/core-items/96c600fa-bc34-4d11-884a-4ca920495546/status \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'
```

## Behavior when Users Service is down
```bash
docker compose stop users-service
```

| Operation                            | Result                                          |
|--------------------------------------|-------------------------------------------------|
| `POST /core/core-items`              | **503** — "Users service is unavailable"        |
| `GET /core/core-items/{id}`          | **200** — works normally (no Users call needed) |
| `PATCH /core/core-items/{id}/status` | **200** — works normally                        |
| `GET /users/{id}`                    | **503** — gateway cannot reach Users Service    |
| `POST /users`                        | **503** — gateway cannot reach Users Service    |

Core Service returns 503 on order creation because it cannot validate `owner_user_id` via `GET http://users-service:8080/users/{id}`.
```bash
docker compose start users-service
```

### Responsibility split

- **Student Kseniia Hanziuk:** Core Service, Users Service, domain/application/infrastructure layers (PR https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/7)
- **Student Sofiia Churikova:** Gateway service, docker-compose.yml (microservice setup), Dockerfile fixes, README (PR https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/8)
