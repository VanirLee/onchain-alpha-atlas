from __future__ import annotations

import random
import threading
import time


class TokenBucket:
    """Thread-safe token bucket with a bounded burst and adaptive slow-down."""

    def __init__(self, rate: float, capacity: float | None = None):
        self.rate = max(0.1, float(rate))
        self.capacity = max(1.0, float(capacity or max(1.0, min(10.0, rate))))
        self.tokens = self.capacity
        self.updated = time.monotonic()
        self.lock = threading.Lock()
        self._cooldown = 1.0

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
                self.updated = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait_s = (1 - self.tokens) / self.rate
            time.sleep(max(0.001, wait_s))

    def penalize(self) -> None:
        with self.lock:
            self.rate = max(0.25, self.rate * 0.75)
            self._cooldown = min(30.0, self._cooldown * 2)
            self.tokens = 0.0

    def recover(self, target_rate: float) -> None:
        with self.lock:
            self.rate = min(target_rate, self.rate * 1.02 + 0.01)
            self._cooldown = max(1.0, self._cooldown * 0.98)

    def backoff(self, attempt: int, retry_after: str | None = None) -> None:
        try:
            hinted = float(retry_after or 0)
        except ValueError:
            hinted = 0.0
        delay = max(hinted, min(30.0, 0.25 * (2**attempt))) + random.uniform(0, 0.25)
        time.sleep(delay)


class EndpointSemaphore:
    def __init__(self, default: int = 8):
        self.default = max(1, int(default))
        self._semaphores: dict[str, threading.BoundedSemaphore] = {}
        self._lock = threading.Lock()

    def for_endpoint(self, endpoint: str) -> threading.BoundedSemaphore:
        with self._lock:
            return self._semaphores.setdefault(endpoint, threading.BoundedSemaphore(self.default))
