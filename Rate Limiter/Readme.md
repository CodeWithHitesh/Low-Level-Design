# Rate Limiter — Low Level Design

## Problem Statement (as asked in interviews)

> Design a thread-safe Rate Limiter that restricts the number of requests a client can make within a time window. Support multiple algorithms and allow switching between them.

---

## Candidate Understanding (first 2–3 minutes)

- Each **client** (identified by `client_id`) has their own request counter/state.
- The limiter returns `True` (allow) or `False` (reject) for each incoming request.
- Different algorithms have different accuracy/memory/burst trade-offs — the interviewer usually asks you to compare them.
- Thread safety is critical: multiple threads may call `allowRequest` for the same client concurrently.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes |
|---|---------|-------------|
| 1 | Fixed Window Counter | `FixedWindowRateLimiter` |
| 2 | Sliding Window Log | `SlidingWindowRateLimiter` |
| 3 | Token Bucket | `TokenBucketRateLimiter` |
| 4 | Uniform interface to swap algorithms | `RateLimiter` (ABC) |
| 5 | Decouple creation from usage | `RateLimiterFactory` — **Factory Pattern** |
| 6 | Thread safety per algorithm | `threading.Lock` on shared state |

### TODO Features (mention but don't code)

- **TODO:** Sliding Window Counter (hybrid of fixed windows — more memory-efficient than log, still accurate)
- **TODO:** Distributed rate limiting (Redis + Lua script for atomic check-and-increment across multiple servers)

---

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | Each limiter class owns one algorithm; `RateLimiterFactory` owns creation; `RateLimiterService` owns facade |
| **OCP** | New algorithms added via `RateLimiter` subclass + factory entry — no existing code changes |
| **DIP** | `RateLimiterService` depends on abstract `RateLimiter`, not concrete algorithm class |
| **Thread Safety** | Per-client `defaultdict(Lock)` isolates concurrent users |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `RateLimiter` ABC → `FixedWindow`, `SlidingWindow`, `TokenBucket` | Swap algorithm at runtime without changing service logic |
| **Factory** | `RateLimiterFactory.create()` | Decouple creation from usage; centralized construction with `**kwargs` |

---

## Algorithm Comparison

| Algorithm | Accuracy | Memory | Burst Handling | Weakness |
|-----------|----------|--------|----------------|----------|
| **Fixed Window** | Low | O(1) per client | Poor | Boundary spike: 2× requests at window edges |
| **Sliding Window Log** | High | O(n) — stores every timestamp | Good | High memory under heavy traffic |
| **Token Bucket** | Medium-High | O(1) per client | Controlled | Burst up to full capacity at once |

---

## Thread Safety Design

Each limiter holds a `defaultdict(threading.Lock)` — one lock per `client_id`. `allowRequest` acquires only the lock for the requesting client, so concurrent requests from different users never block each other.

**Trade-off discussed in interviews:**

| Approach | Pros | Cons |
|----------|------|------|
| **Single global lock** | Simple, easy to reason about | All clients serialize on one lock |
| **Per-client lock (implemented)** | Clients don't block each other | Slightly more memory; `defaultdict` handles creation safely |

---

## How Each Algorithm Works

### Fixed Window
```
Window 1 (0s–10s)   Window 2 (10s–20s)
[req][req][req]...  [req][req][req]...
  count = 3           resets to 0
```
Risk: client sends 5 requests at t=9.9s and 5 at t=10.1s → 10 requests in 0.2s.

### Sliding Window Log
```
now = 15s, window = 10s → keep timestamps in (5s, 15s]
[6s, 8s, 11s, 14s] → count = 4 → allow if limit > 4
```
Evicts stale timestamps on every request. Accurate but stores all timestamps.

### Token Bucket
```
capacity = 5, refill_rate = 1 token/sec
t=0:  tokens=5  → request → tokens=4  ✓
t=0:  tokens=4  → request → tokens=3  ✓
...
t=0:  tokens=0  → request → tokens=0  ✗
t=1:  tokens=1  → request → tokens=0  ✓  (refilled)
```

---

## Class Overview

```
RateLimiter (ABC)
    │  - max_requests: int
    │  - _locks: defaultdict[str, Lock]  (per-client)
    │  - allowRequest(client_id: str) -> bool  [abstract]
    │
    ├── FixedWindowRateLimiter
    │       - window_seconds
    │       - _windows: dict  [client_id -> [window_key, count]]
    │
    ├── SlidingWindowRateLimiter
    │       - window_seconds
    │       - _logs: defaultdict  [client_id -> deque of timestamps]
    │
    └── TokenBucketRateLimiter
            - refill_rate
            - _buckets: dict  [client_id -> [tokens, last_refill_time]]

RateLimiterType (Enum)
    FIXED_WINDOW | SLIDING_WINDOW | TOKEN_BUCKET

RateLimiterFactory
    └── _CLASSES: dict  [RateLimiterType -> class]
    └── create(limiter_type, **kwargs) -> RateLimiter

RateLimiterService          ← main entry point for users
    └── allowRequest(client_id: str) -> bool
```

---

## Edge Cases & Validation

| Scenario | Guard |
|----------|-------|
| First request from unknown client | `defaultdict` creates lock and state automatically |
| Concurrent requests same client | Per-client lock serializes; only one thread mutates state |
| Window boundary spike (Fixed Window) | Known weakness — document as trade-off |
| Clock monotonicity | Uses `time.monotonic()` — immune to NTP/DST jumps |
| Unknown limiter type in factory | `ValueError` raised |
| `max_requests = 0` | All requests blocked (valid edge case) |

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `FixedWindow.allowRequest` | O(1) | O(1) per client |
| `SlidingWindow.allowRequest` | O(k) k = expired entries evicted | O(n) timestamps per client |
| `TokenBucket.allowRequest` | O(1) | O(1) per client |
| Factory creation | O(1) | O(1) |

---

## Extensibility

- **Sliding Window Counter** (hybrid): Weighted average of current + previous fixed window — more memory-efficient than log.
- **Distributed rate limiting**: Redis + Lua script for atomic check-and-increment across multiple servers.
- **Rate limit headers**: Return `X-RateLimit-Remaining`, `X-RateLimit-Reset` alongside the allow/deny decision.
- **Tiered limits**: Different `max_requests` per user plan (free/pro/enterprise) — pass config to factory.
- **Adaptive rate limiting**: Dynamically adjust limits based on server load metrics.

---

## How to Walk Through in the Interview

1. **Clarify** (2 min) — single server or distributed? per-user or global? which algorithm preferred?
2. **Define** the abstract interface first — `allowRequest(client_id) -> bool`.
3. **Code** algorithms in order of complexity: Fixed → Sliding → Token Bucket (5–8 min each).
4. **Add thread safety** — explain lock placement and the single-lock vs per-client trade-off.
5. **Add Factory** — decouple creation, makes algorithm swappable.
6. **Mention** distributed variant with Redis as a follow-up (shows senior-level thinking).
