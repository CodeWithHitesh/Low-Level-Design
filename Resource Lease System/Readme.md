# Resource Lease System — Low Level Design

## Problem Statement (as asked in interviews)

> Design a thread-safe Resource Lease System that manages a fixed pool of identical tokens. Users can request a batch of tokens; if granted, they hold those tokens for exactly one hour (configurable). Tokens automatically expire and return to the pool after the lease duration. Users can also release tokens early.

---

## Candidate Understanding (first 2–3 minutes)

- The pool holds a **fixed number of identical tokens** — no distinction between them.
- A **lease** is a batch grant: one `request_tokens` call grants `n` tokens for a constant duration.
- Each grant gets a unique `grant_id` so a user can hold **multiple concurrent batches**.
- On expiry (or early release), tokens return to the pool and become available for others.
- Thread safety is critical: multiple threads may request/release tokens concurrently.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Class / Mechanism |
|---|---------|----------------------|
| 1 | Initialise pool with configurable size and lease duration | `ResourceLeaseSystem.__init__` |
| 2 | Request `n` tokens; return a unique `grant_id` | `request_tokens` |
| 3 | Release tokens early via `grant_id` | `release_tokens` — **Lazy Deletion** |
| 4 | Auto-expiry with O(1) amortised cost | `_process_expirations` — **FIFO Deque** |
| 5 | Thread safety for all state mutations | `threading.Lock` |
| 6 | Encapsulate grant data | `Grant` dataclass |
| 7 | Custom exceptions for clean error handling | `InsufficientTokensError`, `InvalidGrantError` |

### TODO Features (mention but don't code)

- **TODO:** Per-user token cap — limit how many tokens a single user may hold simultaneously.
- **TODO:** Priority queuing — VIP users bypass the queue and get tokens before regular users.
- **TODO:** Lease renewal — extend an active grant's expiry without releasing and re-requesting.
- **TODO:** Waitlist / blocking `request_tokens` — callers block until tokens become available instead of raising an error.
- **TODO:** Metrics — track utilisation rate, peak concurrent grants, average lease hold time.
- **TODO:** Persistence — snapshot pool state to disk/DB so the system survives restarts.

---

## Algorithmic Approach

### Why a Deque instead of a Min-Heap?

Heap-based expiry is O(log n) per operation. Here, the lease duration is a **strict constant** and `time.monotonic()` is non-decreasing, which means:

```
grant at t=10  → expires at t=10+3600
grant at t=11  → expires at t=11+3600
```

Every new grant *always* expires after all existing ones. Insertion order == expiration order, so a plain FIFO `deque` achieves O(1) append and O(1) popleft — no heap needed.

### Lazy Deletion for Early Returns

Searching and removing a node from the middle of a deque is O(n). Instead:

```
release_tokens()                     _process_expirations() (later)
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

**Lock scope:** The lock is acquired at the start of each public method and released before returning. `_process_expirations` is always called *inside* the held lock, so no re-entry issues arise.

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
    │  - grant_id: str           (UUID)
    │  - user_id: str
    │  - token_count: int
    │  - expiry_timestamp: float (monotonic clock)
    │  + is_expired(now?) → bool

ResourceLeaseSystem
    │  - _total_tokens: int
    │  - _available_tokens: int
    │  - _lease_duration_sec: int
    │  - _expiry_queue: deque[Grant]       ← FIFO, ordered by expiry
    │  - _active_grants: dict[str, Grant]  ← grant_id → Grant
    │  - _lock: threading.Lock
    │
    ├── request_tokens(user_id, n) → grant_id
    │       _process_expirations()
    │       check _available_tokens ≥ n  → raises InsufficientTokensError
    │       uuid4 → Grant → deque.append + dict insert
    │
    ├── release_tokens(user_id, grant_id) → None
    │       _process_expirations()
    │       dict lookup → raises InvalidGrantError if missing/wrong user
    │       del dict entry + restore token count  (lazy deletion)
    │
    ├── get_status() → dict
    │       _process_expirations()
    │       snapshot: total / available / active_grant count
    │
    └── _process_expirations() → None  [internal, called under lock]
            while deque front is expired:
                popleft → still in dict? → reclaim tokens + del entry
                          not in dict?  → ghost, discard silently
```

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `request_tokens` | O(1) amortised | O(1) per grant |
| `release_tokens` | O(1) | — |
| `_process_expirations` | O(k) amortised, where k = expired grants popped | — |
| Overall per-call | **O(1) amortised** | O(G) — G = total live grants |

---

## Extensibility (Verbal Discussion Points)

- **Variable lease durations** → the constant-duration assumption breaks; a **Min-Heap** keyed on `expiry_timestamp` replaces the deque (O(log n) per operation).
- **Distributed pool** → replace the in-process lock with a Redis `DECRBY` + `EXPIRE` or a distributed lease via `SETNX`.
- **Lease renewal** → update `expiry_timestamp` in the dict and append a new entry to the deque; the old entry becomes a ghost — lazy deletion handles it automatically.
- **Waitlist** → use a `threading.Condition` instead of a bare `Lock`; waiting threads call `condition.wait()` and are notified by `release_tokens`.
