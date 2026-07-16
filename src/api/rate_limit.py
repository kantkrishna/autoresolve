import time
from typing import Dict, List

from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    Asynchronous In-Memory Fixed Window Rate Limiter.
    Designed for FastAPI Dependency Injection.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, List[float]] = {}

    async def __call__(self, request: Request) -> bool:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self.clients:
            self.clients[client_ip] = []

        # Clean up old requests (older than 60 seconds)
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip] if now - req_time < 60.0
        ]

        if len(self.clients[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded to protect Kafka buffer. Please backoff.",
                headers={"Retry-After": "60"},
            )

        self.clients[client_ip].append(now)
        return True
