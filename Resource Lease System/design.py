"""Resource Lease System -- Low-Level Design (45-min interview scope)"""

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class ResourceLeaseError(Exception):
    """Base exception for all Resource Lease System errors."""


class InsufficientTokensError(ResourceLeaseError):
    def __init__(self, requested: int, available: int) -> None:
        super().__init__(f"Requested {requested} token(s) but only {available} available.")
        self.requested = requested
        self.available = available


class InvalidGrantError(ResourceLeaseError):
    def __init__(self, grant_id: str, user_id: str) -> None:
        super().__init__(f"Grant '{grant_id}' is not valid for user '{user_id}'.")
        self.grant_id = grant_id
        self.user_id = user_id


# ---------------------------------------------------------------------------
# Domain Model
# ---------------------------------------------------------------------------


@dataclass
class Grant:
    """One batch of tokens leased to a user."""
    grant_id: str
    user_id: str
    token_count: int
    expiry_timestamp: float  # monotonic clock value


# ---------------------------------------------------------------------------
# Core System
# ---------------------------------------------------------------------------


class ResourceLeaseSystem:
    """
    Fixed token pool where every lease has the same constant duration.

    Data structures
    ---------------
    _expiry_queue : deque[Grant]
        FIFO queue ordered by expiry.  Because lease_duration is a strict
        constant, time.monotonic() is non-decreasing, so insertion order ==
        expiration order -- no heap required (O(1) amortised expiry).

    _active_grants : dict[grant_id, Grant]
        Hash map for O(1) grant lookups.

    Lazy deletion
    -------------
    release_tokens() removes the grant from _active_grants and restores the
    token count immediately, but leaves its entry in the deque as a "ghost".
    _process_expirations() silently discards ghosts because their grant_id is
    no longer in _active_grants.
    """

    def __init__(self, total_tokens: int, lease_duration_sec: int = 3600) -> None:
        self._total_tokens: int = total_tokens
        self._available_tokens: int = total_tokens
        self._lease_duration_sec: int = lease_duration_sec

        self._expiry_queue: Deque[Grant] = deque()
        self._active_grants: Dict[str, Grant] = {}
        self._lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_tokens(self, user_id: str, n: int) -> str:
        """Grant n tokens to user_id; return a unique grant_id."""
        with self._lock:
            self._process_expirations()  # reclaim expired tokens first

            if n > self._available_tokens:
                raise InsufficientTokensError(requested=n, available=self._available_tokens)

            grant_id = str(uuid.uuid4())
            grant = Grant(
                grant_id=grant_id,
                user_id=user_id,
                token_count=n,
                expiry_timestamp=time.monotonic() + self._lease_duration_sec,
            )

            self._available_tokens -= n
            self._active_grants[grant_id] = grant
            self._expiry_queue.append(grant)  # O(1); always appended at the tail
            return grant_id

    def release_tokens(self, user_id: str, grant_id: str) -> None:
        """Return tokens early.  Uses lazy deletion -- see class docstring."""
        with self._lock:
            self._process_expirations()

            grant = self._active_grants.get(grant_id)
            if grant is None or grant.user_id != user_id:
                raise InvalidGrantError(grant_id=grant_id, user_id=user_id)

            # Restore tokens immediately; the deque ghost is cleaned lazily.
            self._available_tokens += grant.token_count
            del self._active_grants[grant_id]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_expirations(self) -> None:
        """
        Pop expired grants from the front of the deque.  O(1) amortised.
        Must be called with _lock already held.

        Ghost entries (early-released grants) are skipped: their grant_id is
        absent from _active_grants so no token adjustment is needed.
        """
        now = time.monotonic()
        while self._expiry_queue:
            front = self._expiry_queue[0]
            if front.expiry_timestamp > now:
                break  # all remaining grants expire even later -- stop

            self._expiry_queue.popleft()

            if front.grant_id in self._active_grants:
                # Real expiry: reclaim tokens.
                self._available_tokens += front.token_count
                del self._active_grants[front.grant_id]
            # else: ghost entry -- discard silently.


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import random

    print("=== Scenario 1: grant -> early release -> auto-expiry ===")
    s = ResourceLeaseSystem(total_tokens=10, lease_duration_sec=2)

    gid_alice = s.request_tokens("alice", 4)
    gid_bob   = s.request_tokens("bob",   3)
    print(f"Granted alice=4, bob=3  | available={s._available_tokens}")  # 3

    s.release_tokens("alice", gid_alice)
    print(f"Alice released early    | available={s._available_tokens}")  # 7

    time.sleep(2.1)  # let Bob lease expire naturally
    with s._lock:
        s._process_expirations()
    print(f"After Bob expiry        | available={s._available_tokens}")  # 10

    print()
    print("=== Scenario 2: multi-threaded stress test ===")

    POOL, EACH, LEASE = 100, 5, 3
    stress = ResourceLeaseSystem(total_tokens=POOL, lease_duration_sec=LEASE)
    errors: list[str] = []
    err_lock = threading.Lock()

    def worker(tid: int) -> None:
        user = f"u{tid}"
        try:
            gid = stress.request_tokens(user, EACH)
            time.sleep(random.uniform(0.01, 0.1))
            if tid % 2 == 0:          # half release early, half let expire
                stress.release_tokens(user, gid)
        except InsufficientTokensError as e:
            with err_lock:
                errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(30)]
    for t in threads: t.start()
    for t in threads: t.join()

    print(f"Contention errors (pool exhausted): {len(errors)}")
    print(f"Available after threads finish     : {stress._available_tokens}")

    time.sleep(LEASE + 0.5)
    with stress._lock:
        stress._process_expirations()

    assert stress._available_tokens == POOL, "Token leak detected!"
    assert len(stress._active_grants) == 0,  "Grant leak detected!"
    print(f"After full expiry: available={stress._available_tokens}  active_grants={len(stress._active_grants)}")
    print("All assertions passed -- no leaks.")

