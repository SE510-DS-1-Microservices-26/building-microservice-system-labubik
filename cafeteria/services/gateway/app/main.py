import logging
import os
import uuid

import httpx
from fastapi import FastAPI, Request, Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cafeteria — Gateway", redirect_slashes=False)

CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://core-service:8080")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users-service:8080")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        logger.info("Generated new correlation id: %s", correlation_id)

    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


async def _proxy(request: Request, target_url: str) -> Response:
    target_url = target_url.rstrip("/")

    if request.url.query:
        target_url += f"?{request.url.query}"

    body = await request.body()

    headers = {
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "X-Correlation-Id": request.state.correlation_id,
    }

    accept = request.headers.get("Accept")
    if accept:
        headers["Accept"] = accept

    logger.info(
        "[%s] %s %s -> %s",
        request.state.correlation_id,
        request.method,
        request.url.path,
        target_url,
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Upstream unavailable: %s", exc)
            return Response(
                content='{"detail": "Service unavailable"}',
                status_code=503,
                media_type="application/json",
            )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


@app.api_route("/core/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_core(request: Request, path: str):
    target_url = f"{CORE_SERVICE_URL}/{path}"
    return await _proxy(request, target_url)


@app.api_route("/users", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_users_root(request: Request):
    target_url = f"{USERS_SERVICE_URL}/users"
    return await _proxy(request, target_url)


@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_users(request: Request, path: str):
    target_url = f"{USERS_SERVICE_URL}/users/{path}"
    return await _proxy(request, target_url)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}
