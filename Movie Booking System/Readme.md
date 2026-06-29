# Movie Booking System — Low Level Design

## Problem Statement

> Design a movie ticket booking system where users can browse shows, select seats, and complete a booking. The system must prevent double-booking under concurrent load, handle lock timeouts when users abandon checkout, and support multiple payment methods.

---

## Candidate Understanding (first 2–3 minutes)

- A **Show** is a specific screening of a **Movie** at a **Screen** on a given date/time.
- Each **Seat** in a **Screen** gets a **ShowSeat** per show — this is the runtime entity that carries booking status.
- Status lifecycle: `AVAILABLE → LOCKED → BOOKED` (or back to `AVAILABLE` on timeout/failure).
- Two users selecting the same seat concurrently must be serialized — one must win, one must get a clear error.
- Lock timeout is critical: if a user abandons checkout, the seat must free up for others after a configurable window.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes |
|---|---------|-------------|
| 1 | Domain model hierarchy | `Theater → Screen → Seat`, `Movie`, `Show → ShowSeat` |
| 2 | Per-show seat status tracking | `ShowSeat.status` (AVAILABLE / LOCKED / BOOKED) |
| 3 | Thread-safe seat locking with timeout | `LockService`, `SeatLock`, `LockProvider` |
| 4 | Pluggable lock backend | `LockProvider` (ABC) + `InMemoryLockProvider` |
| 5 | Payment abstraction | `PaymentStrategy` (ABC) + `CardPaymentStrategy` + `PaymentProcessor` |
| 6 | Atomic book flow: lock → pay → confirm | `BookingService.bookSeats` |
| 7 | Lock release on payment failure | `try/except` in `bookSeats` → `releaseSeats` |

### TODO Features (mention but don't code)

- **TODO:** `cancelBooking(booking, user)` — set `CANCELLED`, reset seats, trigger refund.
- **TODO:** `getAvailableShows(movie, city, date)` — separate `ShowService`.
- **TODO:** Notification on booking confirm/cancel — Observer pattern.
- **TODO:** Seat categories (Gold/Silver/Platinum) — `SeatType` enum on `Seat`.
- **TODO:** Distributed lock backend — `RedisLockProvider` with `SET NX PX` + fencing token.

---

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | `LockService` owns lock semantics; `PaymentProcessor` owns payment delegation; `BookingService` only orchestrates |
| **OCP** | New payment methods via `PaymentStrategy` subclass; new lock backends via `LockProvider` subclass — no existing code changes |
| **DIP** | `BookingService` depends on `LockService` and `PaymentProcessor` abstractions, not concrete implementations |
| **LSP** | Any `LockProvider` implementation (in-memory, Redis) is substitutable without changing `LockService` logic |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `PaymentStrategy` → `CardPaymentStrategy`, `UpiPaymentStrategy` | Swap payment method at runtime without changing `BookingService` |
| **Abstract Factory / Provider** | `LockProvider` → `InMemoryLockProvider` | Decouple synchronization primitive from lock business logic; migrate to distributed lock without rewriting `LockService` |

---

## Algorithmic Approach

### Why `ShowSeat` as a junction entity?
The same physical `Seat` is `AVAILABLE` for the 6 PM show and `BOOKED` for the 9 PM show simultaneously. Status must be scoped to a `(show_id, seat_id)` pair — not the seat itself. `ShowSeat` models this as a first-class object with its own status.

### Why per-show mutex + business lock map?
Two-layer design:
1. **`threading.Lock` per show** (from `LockProvider`) — serializes concurrent threads for the same show. Coarse enough to be simple, fine enough to not block different shows.
2. **`SeatLock` map** (`active_locks_by_show`) — business-level metadata: who locked, until when. Allows timeout expiry, same-user extension, and conflict detection.

**Trade-off: show-level vs seat-level lock**

| Approach | Pros | Cons |
|----------|------|------|
| **Per-show lock (implemented)** | Simple, avoids deadlock from lock ordering | Slightly higher contention for popular shows |
| **Per-seat lock** | Lower contention | Risk of deadlock when booking multiple seats; complex lock ordering required |

### Why inline expiry check vs background purge?
Lazy expiry (check on access) keeps the code simple and avoids a background thread. The downside (stale entries in the map for non-requested seats) is acceptable for a 45-minute round. In production, a scheduled sweeper would clear all expired entries periodically.

### Atomic availability + lock in one critical section
Availability check and lock write are both done inside `with self.provider.getShowLock(show_id)`. Without this, two users could both pass the availability check and both attempt to lock — resulting in a double-booking window.

---

## Class Overview

```
Theater
    - id, name
    - screens: List[Screen]

Screen
    - id, number
    - seats: List[Seat]

Seat
    - id, number, base_price

Movie
    - id, name, duration_in_secs

Show
    - id, movie, screen, start_time
    - seats: List[ShowSeat]

ShowSeat                          ← junction entity; runtime seat state
    - id, seat, status: SeatStatus

SeatStatus (Enum)
    AVAILABLE | LOCKED | BOOKED

BookingStatus (Enum)
    CONFIRMED | CANCELLED

User
    - id, name

SeatLock                          ← temporary lock metadata
    - user_id, expires_at

LockProvider (ABC)
    └── getShowLock(show_id) -> Lock

InMemoryLockProvider
    - _show_locks: defaultdict(Lock)
    └── getShowLock(show_id) -> Lock

LockService
    - active_locks_by_show: Dict[show_id, Dict[seat_id, SeatLock]]
    - timeout_seconds: int
    └── lockSeats(show_id, seats, user_id) -> Tuple[bool, Optional[ShowSeat]]
    └── releaseSeats(show_id, seats, user_id) -> None

Booking
    - id, user, show, seats: List[ShowSeat], status: BookingStatus

PaymentStrategy (ABC)
    └── processPayment(amount) -> bool

CardPaymentStrategy
    └── processPayment(amount) -> bool

PaymentProcessor
    - payment_strategy: PaymentStrategy
    └── processPayment(amount) -> bool

BookingService                    ← main orchestrator
    - lock_service, payment_processor
    └── bookSeats(show, seats, user) -> Booking
```

---

## Edge Cases & Validation

| Scenario | Guard |
|----------|-------|
| Two users book same seat concurrently | Availability check + lock write under show-level mutex |
| User abandons checkout (lock expires) | Per-seat expiry check inside `lockSeats`; status reset to `AVAILABLE` |
| Payment fails after lock acquired | `try/except` in `bookSeats` calls `releaseSeats` before re-raising |
| Same user re-selects already-locked seat | `existing.user_id == user_id` → same-user extension allowed, expiry refreshed |
| Seat already `BOOKED` (terminal state) | Rejected at `seat.status == BOOKED` check in `lockSeats` |
| Empty seats list | Passes all checks, returns a `Booking` with no seats — caller should validate before calling |

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `lockSeats(n seats)` | O(n) under show mutex | O(n) new `SeatLock` entries |
| `releaseSeats(n seats)` | O(n) under show mutex | O(1) |
| `bookSeats(n seats)` | O(n) for lock + O(n) for status update | O(1) extra beyond lock |
| `getShowLock` (first access) | O(1) amortised via `defaultdict` | O(shows) total locks held |

---

## Extensibility

- **Distributed deployment**: Replace `InMemoryLockProvider` with a `RedisLockProvider` using `SET key NX PX ttl` + fencing token. No changes to `LockService` or `BookingService`.
- **New payment methods**: Add `UpiPaymentStrategy`, `WalletPaymentStrategy` implementing `PaymentStrategy`. No changes to `BookingService`.
- **Seat pricing tiers**: Add `SeatType` enum (Gold/Silver/Platinum) to `Seat`; pricing logic stays in `base_price` or a `PricingStrategy`.
- **Cancellation & refund**: `cancelBooking` on `BookingService` — set `CANCELLED`, reset `ShowSeat.status = AVAILABLE`, delegate refund to `PaymentProcessor`. Refund policies (full/partial/time-based) modelled as a `RefundStrategy`.
- **Notifications**: Observer pattern on `BookingService`; fire events on confirm/cancel to email/SMS/push subscribers.
- **Show search**: Separate `ShowService.getAvailableShows(movie, city, date)` — keeps `BookingService` focused on transactional flow.

---

## Interviewer Follow-up Probes

| Question | Discussion Points |
|----------|-------------------|
| **What if the payment gateway hangs (timeout, not failure)?** | Set a hard timeout on the payment call. If it exceeds the threshold, treat as failure → release locks. Optionally use an async payment model: return `PENDING`, confirm on callback, use a compensating transaction if callback never arrives. |
| **How do you ensure idempotency on retries?** | Attach an idempotency key (e.g., `user_id + show_id + seat_ids + timestamp hash`) to the payment request. Payment gateway deduplicates on this key. Prevents double-charging if user refreshes or network retries. |
| **How do you prevent lock abuse / starvation?** | Rate-limit `lockSeats` calls per user (e.g., max 3 active lock sets). Track abandoned locks; if a user exceeds an abandonment threshold, add a cooldown before allowing new locks. |
| **UI shows seat as available but server rejects — how to handle?** | Optimistic UI is acceptable. Server is the source of truth — reject with a clear error and ask client to refresh the seat map. Use short-polling or WebSocket push to keep the UI seat map eventually consistent. |
| **How would you generate unique booking IDs across multiple instances?** | Replace `_next_booking_id` counter with Snowflake IDs (timestamp + machine_id + sequence) or database-issued sequences. UUIDs work but are less sortable. |
| **How do you handle show scheduling conflicts on the same screen?** | A `ShowService.createShow()` must validate no time overlap: `new_start < existing_end AND new_end > existing_start`. Enforce under a per-screen lock or a DB unique constraint on `(screen_id, time_range)`. |
| **How would you support dynamic / surge pricing?** | Extract pricing into a `PricingStrategy` that takes `(seat, show, demand_signal)` and returns a price. `BookingService` calls `pricingStrategy.calculatePrice(seat, show)` instead of reading `seat.base_price` directly. |
| **What about partial seat lock failure?** | Current design is all-or-nothing: check all seats first, then lock all. This avoids partial state. If the interviewer pushes for partial success, return `(locked_seats, failed_seats)` and let the client decide whether to proceed with a subset. |
| **How would cancellation work with time-based refund policies?** | Model `RefundPolicy` as a strategy: `FullRefundPolicy` (cancel > 24h before show), `PartialRefundPolicy` (cancel 2–24h), `NoRefundPolicy` (< 2h). `cancelBooking` delegates to the active policy based on `show.start_time - now`. |
