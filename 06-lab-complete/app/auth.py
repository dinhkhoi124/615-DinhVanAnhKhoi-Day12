"""Production-ready, stateless AI agent."""
import json
import logging
import os
import signal
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from redis.exceptions import RedisError

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_and_record_cost
from app.rate_limiter import check_rate_limit
from app.storage import append_history, check_redis, load_history
from utils.mock_llm import ask as llm_ask


logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","message":%(message)s}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = os.getenv("INSTANCE_ID", f"agent-{uuid.uuid4().hex[:8]}")
_is_ready = False
_request_count = 0
_error_count = 0
GRACEFUL_SHUTDOWN_SIGNAL = signal.SIGTERM


def log_event(event: str, **fields) -> None:
    logger.info(json.dumps({"event": event, **fields}))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _is_ready
    log_event("startup", instance=INSTANCE_ID, version=settings.app_version)
    try:
        check_redis()
        _is_ready = True
        log_event("ready", instance=INSTANCE_ID)
    except RedisError as exc:
        logger.error(json.dumps({"event": "startup_failed", "error": str(exc)}))

    # Uvicorn catches SIGTERM and enters this shutdown branch after draining requests.
    yield

    _is_ready = False
    log_event("shutdown", instance=INSTANCE_ID)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    started = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
    except Exception:
        _error_count += 1
        log_event("request_error", method=request.method, path=request.url.path)
        raise

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    log_event(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.time() - started) * 1000, 1),
        instance=INSTANCE_ID,
    )
    return response


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str
    served_by: str
    history_messages: int


@app.get("/")
def root():
    return {"app": settings.app_name, "version": settings.app_version}


@app.post("/ask", response_model=AskResponse)
def ask_agent(body: AskRequest, user_id: str = Depends(verify_api_key)):
    check_rate_limit(user_id)
    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(user_id, input_tokens, 0)

    try:
        append_history(user_id, "user", body.question)
        answer = llm_ask(body.question)
        append_history(user_id, "assistant", answer)
        history = load_history(user_id)
    except RedisError as exc:
        raise HTTPException(503, "Conversation storage unavailable") from exc

    check_and_record_cost(user_id, 0, len(answer.split()) * 2)
    log_event("agent_call", user_id=user_id, instance=INSTANCE_ID)
    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        served_by=INSTANCE_ID,
        history_messages=len(history),
    )


@app.get("/history")
def history(user_id: str = Depends(verify_api_key)):
    try:
        return {"messages": load_history(user_id), "served_by": INSTANCE_ID}
    except RedisError as exc:
        raise HTTPException(503, "Conversation storage unavailable") from exc


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "instance": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    try:
        check_redis()
    except RedisError as exc:
        raise HTTPException(503, "Redis unavailable") from exc
    return {"ready": True, "instance": INSTANCE_ID}


@app.get("/metrics")
def metrics(_user_id: str = Depends(verify_api_key)):
    return {
        "instance": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )