# Practice 7 — Workflow / Saga + Kubernetes Deployment

## Overview

**Workflow:** Place Order saga

- Step 1: Create order in core-service
- Step 2: Confirm order (change status to pending)
- Compensation: If Step 2 fails → cancel the created order

**Services:**

- **core-service** — orders management (CRUD + status transitions)
- **users-service** — user management
- **notification-service** — listens to RabbitMQ events, stores notifications
- **workflow-service** — saga orchestrator, persists workflow state
- **gateway** — API gateway, proxies requests to all services

**Infrastructure:**

- PostgreSQL per service (4 databases)
- RabbitMQ for async messaging
- Kubernetes with Ingress

## Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` configured to use `docker-desktop` context

```bash
kubectl config use-context docker-desktop
```

## Build & Deploy

### 1. Build Docker images

```bash
docker-compose build
```

### 2. Tag images for Kubernetes

```bash
docker tag cafeteria-core-service:latest cafeteria/core-service:latest
docker tag cafeteria-users-service:latest cafeteria/users-service:latest
docker tag cafeteria-notification-service:latest cafeteria/notification-service:latest
docker tag cafeteria-workflow-service:latest cafeteria/workflow-service:latest
docker tag cafeteria-gateway:latest cafeteria/gateway:latest
```

### 3. Deploy to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml 
kubectl apply -f k8s/
```

### 4. Verify pods are running

Wait 2-3 minutes for all pods to start:

```bash
kubectl get pods -n cafeteria
```

Expected output — all pods `1/1 Running`:

```
NAME                                    READY   STATUS    AGE
core-db-0                               1/1     Running   ..m
core-service-...                        1/1     Running   ..m
gateway-...                             1/1     Running   ..m
notification-db-0                       1/1     Running   ..m
notification-service-...                1/1     Running   ..m
rabbitmq-...                            1/1     Running   ..m
users-db-0                              1/1     Running   ..m
users-service-...                       1/1     Running   ..m
workflow-db-0                           1/1     Running   ..m
workflow-service-...                    1/1     Running   ..m
```

Note: application services may restart 2-3 times while waiting for databases to become ready. This is expected behavior.

### 5. Verify services

```bash
kubectl get svc -n cafeteria
```

## How to Reach Gateway

Port-forward the gateway service:

```bash
kubectl port-forward svc/gateway 8080:8080 -n cafeteria
```

Gateway is now accessible at `http://localhost:8080`.

Health check:

```bash
curl http://localhost:8080/health
```

## How to Verify Workflow

### Success Path

```bash
# 1. Create a user
curl -s -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Sofiia"}'
# Save the returned "id" as USER_ID

# 2. Start place-order workflow
curl -s -X POST http://localhost:8080/workflows/place-order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Sofiia",
    "item_name": "Salad",
    "quantity": 1,
    "price": 120.0,
    "owner_user_id": "<USER_ID>"
  }'
# Save the returned "workflow_id" as WORKFLOW_ID

# 3. Check workflow status
curl -s http://localhost:8080/workflows/<WORKFLOW_ID>
```

Expected result for success path:

```json
{
  "workflow_id": "...",
  "type": "place-order",
  "state": "completed",
  "last_error": null
}
```

State transitions: `started` → `order_created` → `order_confirmed` → `completed`

### Failure Path (Compensation)

The compensation path triggers when Step 2 (confirm order) fails. The workflow service catches the error, sets state to
`compensating`, and sends a cancel request to core-service to undo the created order.

State transitions on failure: `started` → `order_created` → `compensating` → `cancelled`

If compensation also fails: `started` → `order_created` → `compensating` → `failed`

The `last_error` field stores the failure reason.

```bash
# Create an order directly
curl -s -X POST http://localhost:8080/core/core-items \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Sofiia",
    "item_name": "Pizza",
    "quantity": 2,
    "price": 150.0,
    "owner_user_id": "<USER_ID>"
  }'

# Get order by id
curl -s http://localhost:8080/core/core-items/<ORDER_ID>

# Update order status
curl -s -X PATCH http://localhost:8080/core/core-items/<ORDER_ID>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'

# Get user by id
curl -s http://localhost:8080/users/<USER_ID>

# Validation error (returns 422)
curl -s -X POST http://localhost:8080/core/core-items \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "", "item_name": "Pizza", "quantity": 0, "price": -10.0, "owner_user_id": "<USER_ID>"}'

# Not found (returns 404)
curl -s http://localhost:8080/workflows/00000000-0000-0000-0000-000000000000
curl -s http://localhost:8080/users/00000000-0000-0000-0000-000000000000
```

## Kubernetes Manifests

All manifests are in the `k8s/` folder:

| File                        | Resources                                       |
|-----------------------------|-------------------------------------------------|
| `namespace.yaml`            | Namespace `cafeteria`                           |
| `configmap.yaml`            | ConfigMap with service URLs, DB hosts/names     |
| `secrets.yaml`              | Secret with DB and RabbitMQ credentials         |
| `rabbitmq.yaml`             | RabbitMQ ConfigMap + Deployment + Service       |
| `core-db.yaml`              | PostgreSQL StatefulSet + PVC + headless Service |
| `users-db.yaml`             | PostgreSQL StatefulSet + PVC + headless Service |
| `notification-db.yaml`      | PostgreSQL StatefulSet + PVC + headless Service |
| `workflow-db.yaml`          | PostgreSQL StatefulSet + PVC + headless Service |
| `core-service.yaml`         | Deployment + Service                            |
| `users-service.yaml`        | Deployment + Service                            |
| `notification-service.yaml` | Deployment + Service                            |
| `workflow-service.yaml`     | Deployment + Service                            |
| `gateway.yaml`              | Deployment + Service (ClusterIP)                |
| `ingress.yaml`              | Ingress (nginx, host: cafeteria.local)          |

Each Deployment includes:

- Environment variables via ConfigMap + Secret
- Readiness probe
- Liveness probe
- Resource requests and limits

Databases use StatefulSets with PersistentVolumeClaims (1Gi each).

## Cleanup

```bash
kubectl delete -f k8s/ -n cafeteria
```

To also remove persistent data:

```bash
kubectl delete pvc --all -n cafeteria
kubectl delete namespace cafeteria
```

## Workflow Service API

| Method | Endpoint                  | Description            |
|--------|---------------------------|------------------------|
| POST   | `/workflows/place-order`  | Start place-order saga |
| GET    | `/workflows/{workflowId}` | Get workflow status    |

### workflow_instances table

| Column      | Type     | Description                        |
|-------------|----------|------------------------------------|
| workflow_id | UUID     | Primary key                        |
| type        | String   | Workflow type (e.g. "place-order") |
| state       | Enum     | Current state                      |
| payload     | JSON     | Request data + order_id            |
| created_at  | DateTime | Creation timestamp                 |
| updated_at  | DateTime | Last update timestamp              |
| last_error  | Text     | Error message (null on success)    |

## Team

**Kseniia Hanziuk** — Workflow saga logic, state persistence, compensation path

**Sofiia Churikova** — Kubernetes manifests, deployment configuration, troubleshooting