"""Middleware for logging full request and response payloads."""

import json
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from src.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log detailed request and response information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log its details."""
        if not settings.bridge_log_payloads:
            return await call_next(request)

        # Log request details
        request_id = f"{time.time():.3f}"
        path = request.url.path
        method = request.method
        
        # Capture request body
        body = await request.body()
        
        # We need to replace the request body because it's been consumed
        async def receive() -> Message:
            return {"type": "http.request", "body": body}
        
        request._receive = receive

        try:
            body_json = json.loads(body) if body else {}
            payload_log = json.dumps(body_json, indent=2)
        except json.JSONDecodeError:
            payload_log = body.decode("utf-8", errors="replace") if body else "<Empty body>"

        logger.info(
            f"[AUDIT] [{request_id}] Incoming {method} {path}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Payload: {payload_log}"
        )

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Capture response body for certain content types
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Replace the response body iterator
        response.body_iterator = iterate_in_chunks(response_body)

        try:
            resp_json = json.loads(response_body) if response_body else {}
            resp_log = json.dumps(resp_json, indent=2) if isinstance(resp_json, dict) else str(resp_json)
        except json.JSONDecodeError:
            resp_log = response_body.decode("utf-8", errors="replace") if response_body else "<Empty body>"

        logger.info(
            f"[AUDIT] [{request_id}] Outgoing {method} {path} - Status: {response.status_code} - Duration: {duration:.3f}s\n"
            f"Response Payload: {resp_log}"
        )

        return response


async def iterate_in_chunks(content: bytes):
    """Helper to iterate over bytes in a single chunk."""
    yield content
