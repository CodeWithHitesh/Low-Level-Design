# Resource Lease System — Low Level Design

## Problem Statement (as asked in interviews)

> Design a thread-safe Resource Lease System that manages a fixed pool of identical tokens. Users can request a batch of tokens; if granted, they hold those tokens for exactly one hour (configurable). Tokens automatically expire and return to the pool after the lease duration. Users can also release tokens early.

---

## Candidate Understanding (first 2–3 minutes)

- The pool holds a **fixed number of identical tokens** — no distinction between them.
- A **lease** is a batch grant: one `requestTokens` call grants `n` tokens for a constant duration.
- Each grant gets a unique `grant_id` so a user can hold **multiple concurrent batches**.
- On expiry (or early release), tokens return to the pool and become available for others.
- Thread safety is critical: multiple threads may request/release tokens concurrently.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Class / Mechanism |
|---|---------|----------------------|
| 1 | Initialise pool with configurable size and lease duration | `ResourceLeaseSystem.__init__` |
| 2 | Request `n` tokens; return a unique `grant_id` | `requestTokens` |
| 3 | Release tokens early via `grant_id` | `releaseTokens` — **Lazy Deletion** |
| 4 | Auto-expiry with O(1) amortised cost | `_processExpirations` — **FIFO Deque** |
| 5 | Thread safety for all state mutations | `threading.Lock` |
| 6 | Encapsulate grant data | `Grant` dataclass |
| 7 | Custom exceptions for clean error handling | `InsufficientTokensError`, `InvalidGrantError` |

### TODO Features (mention but don't code)

- **TODO:** Per-user token cap — limit how many tokens a single user may hold simultaneously.
- **TODO:** Priority queuing — VIP users bypass the queue and get tokens before regular users.
- **TODO:** Lease renewal — extend an active grant's expiry without releasing and re-requesting.
- **TODO:** Waitlist / blocking `requestTokens` — callers block until tokens become available instead of raising an error.
- **TODO:** Metrics — track utilisation rate, peak concurrent grants, average lease hold time.
- **TODO:** Persistence — snapshot pool state to disk/DB so the system survives restarts.

---

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | `ResourceLeaseSystem` owns pool logic; `Grant` is a pure data carrier; exceptions are self-descriptive |
| **OCP** | New expiry policies or priority schemes can be added without modifying existing grant/release logic |
| **DIP** | Callers interact via `requestTokens`/`releaseTokens` interface — internal data structures are hidden |
| **Thread Safety** | Single `threading.Lock` acceptable here (one shared pool); per-entity lock would add unnecessary complexity |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **FIFO Deque + Lazy Deletion** | `_expiry_queue` + `_active_grants` | O(1) amortised expiry without a heap; lazy deletion avoids deque modification on early release |
| **Dataclass** | `Grant` | Clean immutable-style data carrier with named fields |
| **Custom Exception Hierarchy** | `ResourceLeaseError` → `InsufficientTokensError`, `InvalidGrantError` | Callers can catch broadly or narrowly; avoids leaking internal state |

---

## Algorithmic Approach

### Why a Deque instead of a Min-Heap?

Heap-based expiry is O(log n) per operation. Here, the lease duration is a **strict constant** and `time.monotonic()` is non-decreasing, which means:

```
grant at t=10  → expires at t=10+3600
grant at t=11  → expires at t=11+3600
```

Every new grant *always* expires after all existing ones. Insertion order == expiration order, so a plain FIFO `deque` achieves O(1) append and O(1) popleft — no heap needed.

### Why `_processExpirations()` is called inside `releaseTokens()`

This is not about token accounting — tokens are restored correctly either way. It is about **semantic correctness**.

Without the call, a grant that has already expired could still be found in `_active_grants` (because expiry is lazy). The caller would "release" a logically dead grant, which is wrong — the system would appear to accept a no-op as a valid operation and restore tokens that have already been reclaimed.

With the call, expired grants are reclaimed first. If the target grant has expired, the dict lookup returns `None` and `InvalidGrantError` is raised — the correct outcome.

```
_processExpirations()  ← run first; removes logically dead grants
dict lookup             ← if grant gone (expired), raise InvalidGrantError
                          if grant alive (not yet expired), proceed with release
```

### Lazy Deletion for Early Returns

Searching and removing a node from the middle of a deque is O(n). Instead:

```
releaseTokens()                     _processExpirations() (later)
  ├─ del _active_grants[grant_id]        ├─ pop front (ghost entry)
  └─ _available_tokens += n              ├─ grant_id in _active_grants? → NO
                                         └─ discard silently ✓
```

The deque is never searched; the dict lookup is O(1). Tokens are restored **immediately** on early release.

---

## Thread Safety Design

A single `threading.Lock` guards all shared mutable state:

| Shared State | Why It Needs Protection |
|---|---|
| `_available_tokens` | Read-modify-write; race condition without a lock |
| `_active_grants` (dict) | Dict is not thread-safe for concurrent writes |
| `_expiry_queue` (deque) | `append` / `popleft` are individually atomic in CPython but compound operations are not |

**Lock scope:** The lock is acquired at the start of each public method and released before returning. `_processExpirations` is always called *inside* the held lock, so no re-entry issues arise.

---

## Exception Hierarchy

```
ResourceLeaseError          ← base
├── InsufficientTokensError    requested=n, available=k
└── InvalidGrantError          grant_id, user_id
```

Custom exceptions allow callers to handle each failure mode independently without catching broad `Exception` or `ValueError`.

---

## Class Overview

```
Grant (dataclass)
    │  - grant_id: int            (incrementing counter)
    │  - user_id: str
    │  - token_count: int
    │  - expiry_timestamp: float (monotonic clock)

ResourceLeaseSystem
    │  - _total_tokens: int
    │  - _available_tokens: int
    │  - _lease_duration_sec: int
    │  - _expiry_queue: deque[Grant]       ← FIFO, ordered by expiry
    │  - _active_grants: dict[str, Grant]  ← grant_id → Grant
    │  - _lock: threading.Lock
    │
    ├── requestTokens(user_id, n) → grant_id
    │       _processExpirations()
    │       check _available_tokens ≥ n  → raises InsufficientTokensError
    │       increment counter → Grant → deque.append + dict insert
    │
    ├── releaseTokens(user_id, grant_id) → None
    │       _processExpirations()
    │       dict lookup → raises InvalidGrantError if missing/wrong user
    │       del dict entry + restore token count  (lazy deletion)
    │
    ├── getStatus() → dict
    │       _processExpirations()
    │       snapshot: total / available / active_grant count
    │
    └── _processExpirations() → None  [internal, called under lock]
            while deque front is expired:
                popleft → still in dict? → reclaim tokens + del entry
                          not in dict?  → ghost, discard silently
```

---

## Edge Cases & Validation

### `releaseTokens` — information hiding in `InvalidGrantError`

Two distinct failure modes exist:
- `grant_id` does not exist in `_active_grants`
- `grant_id` exists but belongs to a different user

Both raise **the same `InvalidGrantError` with the same message** intentionally. If the two cases were distinguished (e.g., `GrantNotFoundError` vs `UnauthorizedReleaseError`), a caller could probe whether a `grant_id` is valid but owned by someone else — an information-leakage risk in a multi-tenant system.

The rule: **never confirm the existence of a resource to a caller who doesn't own it.**

### `grant_id` — incrementing counter vs UUID

The current implementation uses a simple incrementing counter (`grant-1`, `grant-2`, …) instead of `uuid.uuid4()`.

**Why UUID is strictly safer:**  
UUIDs are unpredictable (122 bits of entropy), so a caller cannot enumerate other users' grant IDs even if they know the scheme. A counter is sequential and trivially guessable, making it an **IDOR (Insecure Direct Object Reference)** risk in public-facing APIs.

**Why the counter is acceptable here:**  
The second argument to `releaseTokens` is `user_id`, and the code checks `grant.user_id != user_id` before acting. Both "grant not found" and "wrong owner" collapse into the same `InvalidGrantError`, so even if an attacker guesses a valid `grant_id`, they cannot release it without also knowing the correct `user_id`. The `user_id` check is the compensating control that neutralises the IDOR risk.

**Summary:**

| ID scheme | IDOR risk | Thread-safe? | Readable in logs |
|-----------|-----------|--------------|------------------|
| UUID | None | Yes (no shared state) | Hard |
| Counter (`int`) | Mitigated by `user_id` check | Yes (incremented under lock) | Easy |

For a real production API, prefer UUID. For an in-memory interview solution, the counter is simpler to reason about and safe given the existing ownership check.

---

### `__init__` — pool configuration

| Input | Behaviour |
|---|---|
| `total_tokens <= 0` | `ValueError` — a pool of zero or negative tokens is nonsensical |
| `lease_duration_sec <= 0` | `ValueError` — a non-positive duration would expire grants instantly or invert ordering |

### `requestTokens` — token count `n`

| Input | Behaviour |
|---|---|
| `n <= 0` | `ValueError` raised **before** acquiring the lock — no wasted contention |
| `n > available` | `InsufficientTokensError` (existing) |

The `n <= 0` check is done outside the lock intentionally. It is a pure input validation that requires no shared state — holding the lock while checking it would unnecessarily block other threads.

### `Grant` — why not `frozen=True`?

`Grant` is left mutable on purpose. The planned **lease renewal** TODO requires updating `expiry_timestamp` in-place on an existing grant. A `frozen=True` dataclass would force deleting and recreating the grant object, which complicates both the dict and the deque (the deque holds a reference; a new object would create a stale ghost immediately).

If lease renewal is never implemented, converting to `frozen=True` is a safe and recommended improvement — it prevents accidental mutation of grant data.

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `requestTokens` | O(1) amortised | O(1) per grant |
| `releaseTokens` | O(1) | — |
| `_processExpirations` | O(k) amortised, where k = expired grants popped | — |
| Overall per-call | **O(1) amortised** | O(G) — G = total live grants |

---

## Extensibility (Verbal Discussion Points)

- **Variable lease durations** → the constant-duration assumption breaks; a **Min-Heap** keyed on `expiry_timestamp` replaces the deque (O(log n) per operation).

  `heapq` compares heap elements directly, so `Grant` needs a `__lt__` method; otherwise pushing two `Grant` objects raises `TypeError`.

  ```python
  import heapq

  @dataclass
  class Grant:
      grant_id: int
      user_id: str
      token_count: int
      expiry_timestamp: float

      def __lt__(self, other: "Grant") -> bool:
          # Min-heap orders by soonest expiry first
          return self.expiry_timestamp < other.expiry_timestamp

  # In ResourceLeaseSystem.__init__:
  self._expiry_heap: list[Grant] = []   # heapq min-heap; replaces _expiry_queue

  # In requestTokens (variable duration passed as argument):
  grant = Grant(grant_id=..., user_id=..., token_count=n,
                expiry_timestamp=time.monotonic() + lease_duration_sec)
  heapq.heappush(self._expiry_heap, grant)

  # In _processExpirations:
  while self._expiry_heap and self._expiry_heap[0].expiry_timestamp <= now:
      front = heapq.heappop(self._expiry_heap)
      if front.grant_id in self._active_grants:
          self._available_tokens += front.token_count
          del self._active_grants[front.grant_id]
  ```

  The constant-duration deque stays O(1) because insertion order == expiry order. The heap is only needed when different grants can have different durations.
- **Distributed pool** → replace the in-process lock with a Redis `DECRBY` + `EXPIRE` or a distributed lease via `SETNX`.
- **Lease renewal** → update `expiry_timestamp` in the dict and append a new entry to the deque; the old entry becomes a ghost — lazy deletion handles it automatically.
- **Waitlist** → use a `threading.Condition` instead of a bare `Lock`; waiting threads call `condition.wait()` and are notified by `releaseTokens`.
