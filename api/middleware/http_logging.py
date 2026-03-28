"""ASGI middleware: log incoming HTTP requests and responses (structured logs)."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterable

import structlog
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger(__name__)

_MAX_BODY_BYTES = 16_384
_SENSITIVE_HEADER_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "proxy-authorization",
    }
)


def _truncate_bytes(data: bytes, max_len: int = _MAX_BODY_BYTES) -> str:
    if not data:
        return ""
    text = data.decode("utf-8", errors="replace")
    if len(data) > max_len:
        return text[:max_len] + f"... (truncated, {len(data)} bytes total)"
    return text


def _safe_headers(raw_headers: Iterable[tuple[bytes, bytes]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in raw_headers:
        key = k.decode("latin-1").lower()
        name = k.decode("latin-1")
        if key in _SENSITIVE_HEADER_KEYS:
            out[name] = "[REDACTED]"
        else:
            out[name] = v.decode("latin-1", errors="replace")
    return out


def _safe_headers_mapping(headers: Headers) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _SENSITIVE_HEADER_KEYS:
            out[key] = "[REDACTED]"
        else:
            out[key] = value
    return out


async def _buffer_response(response: Response) -> tuple[bytes, Response]:
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    body = b"".join(chunks)
    new_response = Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )
    return body, new_response


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each request/response pair with timing, request id, and redacted headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            body_bytes = await request.body()

            async def receive() -> dict[str, bytes | bool]:
                return {"type": "http.request", "body": body_bytes, "more_body": False}

            request = Request(request.scope, receive)

            client = request.client.host if request.client else None
            log.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                query=str(request.url.query) if request.url.query else None,
                client=client,
                headers=_safe_headers(request.scope.get("headers") or ()),
                body=_truncate_bytes(body_bytes),
            )

            start = time.perf_counter()
            try:
                response = await call_next(request)
                resp_body, response = await _buffer_response(response)
                response.headers["X-Request-ID"] = request_id
            except Exception:
                duration_ms = (time.perf_counter() - start) * 1000
                log.exception("http.response.error", duration_ms=round(duration_ms, 3))
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            log.info(
                "http.response",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 3),
                headers=_safe_headers_mapping(response.headers),
                body=_truncate_bytes(resp_body),
            )
            return response
        finally:
            structlog.contextvars.clear_contextvars()
