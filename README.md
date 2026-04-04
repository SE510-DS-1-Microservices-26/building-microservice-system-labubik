# Cafeteria

## Core Item

**Order** — the main aggregate. Fields: `id`, `customer_name`, `item_name`, `quantity`, `price`, `total`, `status`, `owner_user_id`.

## Domain Rules

1. Customer name cannot be empty
2. Quantity must be positive (> 0)
3. Price must be positive (> 0)
4. Status transitions: `created → pending → confirmed`, `any → cancelled`
5. Cannot cancel an already cancelled order

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

| Component | Responsibility |
|-----------|---------------|
| Gateway | Routes requests, adds `X-Correlation-Id` |
| Core Service | Owns Order and business rules |
| Users Service | Owns user/profile data |
| Notification Service | Listens to RabbitMQ events, stores notifications |
| Workflow Service | Saga orchestrator, persists workflow state |

Data ownership: services communicate only via HTTP; each service writes only to its own database.

## How to Run

### Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/cafeteria"
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

### With Docker Compose

```bash
docker compose up --build
docker compose exec app alembic upgrade head
```

Starts 8 containers: `rabbitmq`, `core-db`, `users-db`, `notification-db`, `core-service`, `users-service`, `notification-service`, `gateway`.

### With Kubernetes

```bash
docker-compose build
docker tag cafeteria-core-service:latest cafeteria/core-service:latest
docker tag cafeteria-users-service:latest cafeteria/users-service:latest
docker tag cafeteria-notification-service:latest cafeteria/notification-service:latest
docker tag cafeteria-workflow-service:latest cafeteria/workflow-service:latest
docker tag cafeteria-gateway:latest cafeteria/gateway:latest

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

Access the gateway via port-forward:

```bash
kubectl port-forward svc/gateway 8080:8080 -n cafeteria
```

Cleanup:

```bash
kubectl delete -f k8s/ -n cafeteria
kubectl delete pvc --all -n cafeteria
kubectl delete namespace cafeteria
```

## Service URLs

| Service | Direct | Via Gateway |
|---------|--------|-------------|
| Gateway | `http://localhost:8080` | — |
| Core Service | `http://localhost:8081` | `http://localhost:8080/core/` |
| Users Service | `http://localhost:8082` | `http://localhost:8080/users/` |
| Notification Service | `http://localhost:8083` | — |
| RabbitMQ Management | `http://localhost:15672` | — (guest/guest) |

## API Endpoints

### Users Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create a user |
| GET | `/users/{id}` | Get user by ID |

### Core Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/core-items` | Create an order |
| GET | `/core-items/{id}` | Get order by ID |
| PATCH | `/core-items/{id}/status` | Update order status |

### Workflow Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflows/place-order` | Start place-order saga |
| GET | `/workflows/{workflowId}` | Get workflow status |

### Notification Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | List stored notifications |

## API Examples

```bash
# Health check
curl http://localhost:8080/health

# Create a user
curl -X POST http://localhost:8080/users/ \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Anna"}'

# Create an order
curl -X POST http://localhost:8080/core/core-items \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Anna",
    "item_name": "Salad",
    "quantity": 1,
    "price": 150.50,
    "owner_user_id": "<USER_ID>"
  }'

# Get an order
curl http://localhost:8080/core/core-items/<ORDER_ID>

# Update order status
curl -X PATCH http://localhost:8080/core/core-items/<ORDER_ID>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'

# Start place-order workflow
curl -X POST http://localhost:8080/workflows/place-order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Anna",
    "item_name": "Salad",
    "quantity": 1,
    "price": 120.0,
    "owner_user_id": "<USER_ID>"
  }'

# Check workflow status
curl http://localhost:8080/workflows/<WORKFLOW_ID>

# Check notifications
curl http://localhost:8083/notifications
```

## Running Tests

```bash
pytest tests/ -v
```

## Event-Driven Notifications

When an order is created, Core Service publishes a `core-item.created` event to RabbitMQ (exchange: `core`, routing key: `core-item.created`). Notification Service consumes from the `notification.core-item.created` queue and stores the notification. Idempotency is ensured by using `event_id` as the primary key — duplicates are silently ignored.

## Workflow / Saga

The **Place Order** saga is orchestrated by Workflow Service:

1. Create order in Core Service
2. Confirm order (change status to `pending`)

If step 2 fails, compensation runs: cancel the created order.

State transitions on success: `started → order_created → order_confirmed → completed`

State transitions on failure: `started → order_created → compensating → cancelled` (or `failed` if compensation also fails)

## Correlation ID

Every request gets an `X-Correlation-Id` header. If the client sends one, it is reused; otherwise the gateway generates a new UUID. This ID propagates through all HTTP calls between services and into RabbitMQ message headers.

## Resiliency

All inter-service HTTP calls have a 5-second timeout and retry up to 3 attempts (1-second wait, only on transient errors via `tenacity`). If a downstream service is unavailable, 503 is returned.

When Users Service is down: order creation returns 503 (cannot validate user), but reading/updating existing orders works normally.

## Kubernetes

### Scaling

Core Service runs with 3 replicas. All deployments use `RollingUpdate` strategy — core-service with `maxUnavailable: 1`, `maxSurge: 1`; other services with `maxUnavailable: 0`, `maxSurge: 1`.

### Resource Limits

| Service | CPU req | CPU limit | Mem req | Mem limit |
|---------|---------|-----------|---------|-----------|
| core-service | 100m | 300m | 128Mi | 256Mi |
| users-service | 100m | 300m | 128Mi | 256Mi |
| notification-service | 100m | 300m | 128Mi | 256Mi |
| workflow-service | 100m | 300m | 128Mi | 256Mi |
| gateway | 50m | 200m | 64Mi | 128Mi |

### Manifests

All manifests are in `k8s/`: namespace, configmap, secrets, per-service deployments with readiness/liveness probes, StatefulSets with PVCs (1Gi each) for databases, RabbitMQ deployment, and nginx Ingress (`cafeteria.local`).

### Verification

```bash
# Check pods
kubectl get pods -n cafeteria

# Check core-service replicas
kubectl get pods -l app=core-service -n cafeteria

# Verify correlation ID
curl -v -H "X-Correlation-Id: test-123" http://localhost:8080/core/core-items

# Rolling update / rollback
kubectl set image deployment/core-service core-service=cafeteria/core-service:v2 -n cafeteria
kubectl rollout status deployment/core-service -n cafeteria
kubectl rollout undo deployment/core-service -n cafeteria
```
