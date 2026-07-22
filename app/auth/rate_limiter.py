import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status

class InMemoryRateLimiter:
    def __init__(self):
        self._records: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 5,
        window_seconds: int = 60,
        custom_message: str = None
    ):
        now = time.time()
        timestamps = self._records[identifier]

        # Filter out timestamps outside the sliding window
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        self._records[identifier] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            retry_after = int(window_seconds - (now - valid_timestamps[0]))
            retry_after = max(1, retry_after)
            msg = custom_message or f"Too many requests. Please wait {retry_after} seconds before trying again."
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=msg,
                headers={"Retry-After": str(retry_after)}
            )

        self._records[identifier].append(now)

rate_limiter = InMemoryRateLimiter()

def get_client_ip(request: Request) -> str:
    """Extract client IP address handling proxies & Render X-Forwarded-For header."""
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
