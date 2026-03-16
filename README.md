# Cafeteria — Practice 4

## Theme
**Cafeteria Food Delivery**
- **Core Item**: `Order`
- **Core Action**: `CreateOrder`

---

## Domain Rules
1. Customer name cannot be empty
2. Quantity must be positive (> 0)
3. Price must be positive (> 0)
4. Status transitions are restricted: `created → pending → confirmed`, `any → cancelled`
5. Cannot cancel an already cancelled order

---

## Project Structure
```
cafeteria/
├── app/
│   ├── api/
│   │   └── orders.py
│   ├── core/
│   │   ├── domain/
│   │   │   └── order.py
│   │   ├── application/
│   │   │   ├── interfaces.py
│   │   │   └── order_service.py
│   │   └── infrastructure/
│   │       ├── database.py
│   │       └── order_repository.py
│   └── main.py
├── alembic/
├── tests/
│   ├── test_domain.py
│   ├── test_service.py
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## How to Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/cafeteria"
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

---

## How to Run with Docker
```bash
docker compose up --build
docker compose exec app alembic upgrade head
```

---

## API Examples
```bash
# Health check
curl http://localhost:8080/health

# Create order
curl -X POST http://localhost:8080/core-items \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Sofiia", "item_name": "Salad", "quantity": 1, "price": 150.50}'

# Get order
curl http://localhost:8080/core-items/<order-id>

# Update status
curl -X PATCH http://localhost:8080/core-items/<order-id>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'
```

---

## Running Tests
```bash
pytest tests/ -v
```

---

## Team Workflow

### Role Split
- **Student Sofiia Churikova**: domain layer, application layer, unit tests, README (PR #1 https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/1, PR #2 https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/2, PR #3 https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/3)
- **Student Kseniia Hanziuk**: infrastructure, API, Docker, migrations, unit tests (PR #4 https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/4, PR #5 https://github.com/SE510-DS-1-Microservices-26/building-microservice-system-labubik/pull/5)
