from abc import ABC, abstractmethod
from enum import Enum
from typing import List
from collections import defaultdict, deque
import threading
import time


class RateLimiter(ABC):
    """Abstract rate limiter with per-client lock isolation."""

    def __init__(self, max_requests: int):
        self.max_requests = max_requests
        self._locks: defaultdict = defaultdict(threading.Lock)

    def _getLock(self, client_id: str) -> threading.Lock:
        return self._locks[client_id]

    @abstractmethod
    def allowRequest(self, client_id: str) -> bool:
        pass


class FixedWindowRateLimiter(RateLimiter):
    """Counts requests per fixed time window."""

    def __init__(self, max_requests: int, window_seconds: int, **kwargs):
        super().__init__(max_requests)
        self.window_seconds = window_seconds
        self._windows: dict = {}   # client_id -> [window_key, count]

    def allowRequest(self, client_id: str) -> bool:
        current_window = int(time.monotonic() // self.window_seconds)

        with self._getLock(client_id):
            entry = self._windows.get(client_id)
            if entry is None or entry[0] != current_window:
                self._windows[client_id] = [current_window, 1]
                return True

            if entry[1] >= self.max_requests:
                return False
            entry[1] += 1
            return True


class SlidingWindowRateLimiter(RateLimiter):
    """Tracks exact request timestamps within a sliding window."""

    def __init__(self, max_requests: int, window_seconds: int, **kwargs):
        super().__init__(max_requests)
        self.window_seconds = window_seconds
        self._logs: defaultdict = defaultdict(deque)

    def allowRequest(self, client_id: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._getLock(client_id):
            log = self._logs[client_id]
            while log and log[0] <= cutoff:
                log.popleft()

            if len(log) >= self.max_requests:
                return False

            log.append(now)
            return True


class TokenBucketRateLimiter(RateLimiter):
    """Refills tokens at a steady rate; requests consume one token."""

    def __init__(self, max_requests: int, refill_rate: float, **kwargs):
        super().__init__(max_requests)
        self.refill_rate = refill_rate
        self._buckets: dict = {}   # client_id -> [tokens, last_refill_time]

    def _refill(self, bucket: list, now: float) -> list:
        existingTokens, lastRefillTime = bucket
        
        elapsed_seconds = int(now - lastRefillTime)
        updatedTokens = min(self.max_requests, existingTokens + elapsed_seconds * self.refill_rate)
        
        bucket = [updatedTokens, lastRefillTime + elapsed_seconds]
        return bucket

    def allowRequest(self, client_id: str) -> bool:
        now = time.monotonic()

        with self._getLock(client_id):
            bucket = self._buckets.get(client_id)
            if bucket is None:
                self._buckets[client_id] = [self.max_requests - 1, now]
                return True

            tokens, _ = self._refill(bucket, now)

            if tokens < 1:
                return False

            bucket[0] -= 1
            return True


class RateLimiterType(Enum):
    """Supported rate limiter algorithm types."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimiterFactory:
    """Creates rate limiter instances by type."""

    _CLASSES = {
        RateLimiterType.FIXED_WINDOW:   FixedWindowRateLimiter,
        RateLimiterType.SLIDING_WINDOW: SlidingWindowRateLimiter,
        RateLimiterType.TOKEN_BUCKET:   TokenBucketRateLimiter,
    }

    @staticmethod
    def create(limiter_type: RateLimiterType, **kwargs) -> RateLimiter:
        cls = RateLimiterFactory._CLASSES.get(limiter_type)
        if not cls:
            raise ValueError(f"Unknown limiter type: {limiter_type}")
        return cls(**kwargs)


class RateLimiterService:
    """Facade that delegates to a configured rate limiter."""

    def __init__(self, limiter_type: RateLimiterType, **kwargs):
        self._limiter = RateLimiterFactory.create(limiter_type, **kwargs)

    def allowRequest(self, client_id: str) -> bool:
        return self._limiter.allowRequest(client_id)


if __name__ == "__main__":
    print("=== Token Bucket (max=3, refill=1/s) ===")
    service = RateLimiterService(RateLimiterType.TOKEN_BUCKET, max_requests=3, refill_rate=1)
    for i in range(5):
        result = service.allowRequest("user_1")
        print(f"  user_1 request {i + 1}: {'ALLOWED' if result else 'BLOCKED'}")

    print("\n=== Fixed Window (max=2, window=60s) — two different users ===")
    service = RateLimiterService(RateLimiterType.FIXED_WINDOW, max_requests=2, window_seconds=60)
    for i in range(3):
        r1 = service.allowRequest("user_1")
        r2 = service.allowRequest("user_2")
        print(f"  user_1 request {i + 1}: {'ALLOWED' if r1 else 'BLOCKED'} | "
              f"user_2 request {i + 1}: {'ALLOWED' if r2 else 'BLOCKED'}")

    print("\n=== Sliding Window (max=3, window=10s) ===")
    service = RateLimiterService(RateLimiterType.SLIDING_WINDOW, max_requests=3, window_seconds=10)
    for i in range(5):
        result = service.allowRequest("user_1")
        print(f"  user_1 request {i + 1}: {'ALLOWED' if result else 'BLOCKED'}")

