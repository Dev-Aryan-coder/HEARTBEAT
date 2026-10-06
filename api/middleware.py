import time
import json
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import threading

logger = logging.getLogger("HEARTBEAT_RATELIMIT")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 20):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.user_records = defaultdict(list)
        self.lock = threading.Lock()

    async def _extract_user_id(self, request: Request) -> str:
        """Extract user_id from query params or POST body.
        ISSUE 32 FIX: Read user_id from JSON body for POST requests."""
        # First check query params
        user_id = request.query_params.get("user_id")
        if user_id:
            return user_id

        # For POST requests, try to read from body
        if request.method == "POST":
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    uid = data.get("user_id") or data.get("chat_id", "anonymous")
                    return str(uid)
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Could not parse body for rate limiting: {str(e)}")

        # Fallback: use client IP as identifier
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    async def dispatch(self, request: Request, call_next):
        # ISSUE 2.3 FIX: Rate Limiting to prevent LLM spam
        if request.url.path == "/api/message":
            user_id = await self._extract_user_id(request)

            now = time.time()
            with self.lock:
                # Clean old records
                self.user_records[user_id] = [
                    t for t in self.user_records[user_id] if now - t < 60
                ]

                if len(self.user_records[user_id]) >= self.requests_per_minute:
                    logger.warning(f"Rate limit exceeded for user: {user_id}")
                    raise HTTPException(
                        status_code=429,
                        detail="Subconscious overloaded. Please wait 60 seconds."
                    )

                self.user_records[user_id].append(now)

        response = await call_next(request)
        return response
