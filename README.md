## Practice 8 — Production Hardening

#### Correlation ID

We added correlation ID propagation across all services. The idea is simple — every request that enters the system gets a unique `X-Correlation-Id` header. If the client already sends one, we reuse it. If not, the middleware generates a new UUID.

This correlation ID travels through the whole system:
- Gateway reads/generates it and forwards to downstream services
- Each service (core, users, workflow, notification) has a middleware that picks it up and logs it
- When services talk to each other via HTTP, they pass it in headers
- When publishing messages to RabbitMQ, the correlation ID goes into message headers too
- The consumer on the notification-service side reads it back

#### Resiliency

All inter-service HTTP calls now have timeouts and retries configured:
- Timeout is set to 5 seconds on all httpx calls
- Retry is done via `tenacity` — up to 3 attempts with 1 second wait, only retries on transient network errors
- If a downstream service is unavailable, we return 503

This covers:
- core-service calling users-service for user validation
- workflow-service calling core-service for order creation/confirmation
- gateway proxying requests to all services (10s timeout, 503 on failure)

#### Kubernetes Scaling

We scaled core-service to 3 replicas and added explicit `RollingUpdate` strategy to all deployments.

For core-service we set `maxUnavailable: 1` and `maxSurge: 1`, so during updates at least 2 out of 3 pods are always available. For other services (1 replica each) we use `maxUnavailable: 0` and `maxSurge: 1` — Kubernetes spins up a new pod first before killing the old one.

All deployments already had readiness/liveness probes and resource limits from Practice 7.

### How to verify

Scale:
```bash
kubectl get pods -l app=core-service -n cafeteria
# should show 3 pods
```

Correlation ID:
```bash
curl -v -H "X-Correlation-Id: my-test-id" \
  http://localhost:8080/core/core-items

# check that response has X-Correlation-Id: my-test-id
kubectl logs -l app=core-service -n cafeteria | grep "my-test-id"
```

Rolling update and rollback:
```bash
kubectl set image deployment/core-service core-service=cafeteria/core-service:v2 -n cafeteria
kubectl rollout status deployment/core-service -n cafeteria
kubectl rollout undo deployment/core-service -n cafeteria
```

Multiple pods serving traffic:
```bash
kubectl logs -l app=core-service -n cafeteria --prefix | head -20
```

### Resource limits

| Service              | CPU req | CPU limit | Mem req | Mem limit |
|----------------------|---------|-----------|---------|-----------|
| core-service         | 100m    | 300m      | 128Mi   | 256Mi     |
| users-service        | 100m    | 300m      | 128Mi   | 256Mi     |
| notification-service | 100m    | 300m      | 128Mi   | 256Mi     |
| workflow-service     | 100m    | 300m      | 128Mi   | 256Mi     |
| gateway              | 50m     | 200m      | 64Mi    | 128Mi     |

### Team

**Kseniia Hanziuk** — Correlation ID middleware and propagation in gateway and core-service, resiliency policies for core-service, RabbitMQ correlation ID

**Sofiia Churikova** — Kubernetes scaling and RollingUpdate strategy, correlation ID middleware for remaining services, resiliency for workflow-service