from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock


class SeatStatus(Enum):
    """Lifecycle states for a seat within a specific show."""

    BOOKED = "BOOKED"
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"


class BookingStatus(Enum):
    """Terminal states for a completed booking."""

    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass
class Theater:
    """Physical venue containing one or more screens."""

    id: int
    name: str
    screens: List['Screen']


@dataclass
class Screen:
    """Single auditorium within a theater."""

    id: int
    number: int
    seats: List['Seat']


@dataclass
class Seat:
    """Physical seat with a fixed base price."""

    id: int
    number: int
    base_price: float


@dataclass
class Movie:
    """Film metadata."""

    id: int
    name: str
    duration_in_secs: int


@dataclass
class Show:
    """A specific screening of a movie on a screen at a given time."""

    id: int
    movie: Movie
    screen: Screen
    start_time: datetime
    seats: List["ShowSeat"]


@dataclass
class User:
    """Registered user who can book tickets."""

    id: int
    name: str


@dataclass
class ShowSeat:
    """Junction entity tracking per-show seat availability."""

    id: int
    seat: Seat
    status: SeatStatus


@dataclass
class SeatLock:
    """Temporary lock metadata for a seat held during checkout."""

    user_id: int
    expires_at: datetime


@dataclass
class Booking:
    """Confirmed or cancelled reservation linking user, show, and seats."""

    id: int
    user: User
    show: Show
    seats: List[ShowSeat]
    status: BookingStatus


class LockProvider(ABC):
    """Abstraction for obtaining a per-show threading lock."""

    @abstractmethod
    def getShowLock(self, show_id: int) -> Lock:
        """Return a context-manageable lock for this show."""
        pass


class InMemoryLockProvider(LockProvider):
    """Thread-safe in-memory lock provider using defaultdict."""

    def __init__(self) -> None:
        self._show_locks: defaultdict = defaultdict(Lock)

    def getShowLock(self, show_id: int) -> Lock:
        return self._show_locks[show_id]


class LockService:
    """Manages per-show seat locks with configurable timeout and lazy expiry."""

    def __init__(self, provider: LockProvider, timeout_seconds: int = 300) -> None:
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        # show_id -> physical_seat_id -> seat lock metadata
        self.active_locks_by_show: defaultdict[int, Dict[int, SeatLock]] = defaultdict(dict)

    def _purgeExpiredLocks(self, show_map: Dict[int, SeatLock], now: datetime) -> None:
        """Remove expired lock entries. LOCKED/AVAILABLE are never persisted on ShowSeat,
        so purging only needs to touch this service's own hold map."""
        expired = [seat_id for seat_id, lock in show_map.items() if lock.expires_at <= now]
        for seat_id in expired:
            del show_map[seat_id]

    def lockSeats(
        self, show_id: int, seats: List[ShowSeat], user_id: int
    ) -> Tuple[bool, Optional[ShowSeat]]:
        """Atomically lock requested seats for a user; returns (success, conflicting_seat).

        BOOKED is the only status persisted on ShowSeat, so the booked check reads
        seat.status directly. LOCKED/AVAILABLE are derived purely from this service's
        own hold map, so no other show seats need to be passed in or mutated.
        """
        now = datetime.now()

        with self.provider.getShowLock(show_id):
            show_map = self.active_locks_by_show[show_id]
            self._purgeExpiredLocks(show_map, now)

            for seat in seats:
                if seat.status == SeatStatus.BOOKED:
                    return False, seat
                existing_lock = show_map.get(seat.seat.id)
                if existing_lock and existing_lock.user_id != user_id:
                    return False, seat

            expiry = now + timedelta(seconds=self.timeout_seconds)
            for seat in seats:
                show_map[seat.seat.id] = SeatLock(user_id=user_id, expires_at=expiry)

            return True, None

    def releaseSeats(self, show_id: int, seats: List[ShowSeat], user_id: int) -> None:
        """Release locks held by user_id. BOOKED seats are untouched; unbooked seats
        simply lose their hold entry and become available again."""
        with self.provider.getShowLock(show_id):
            show_map = self.active_locks_by_show.get(show_id, {})
            for seat in seats:
                existing_lock = show_map.get(seat.seat.id)
                if existing_lock and existing_lock.user_id == user_id:
                    del show_map[seat.seat.id]


class PaymentStrategy(ABC):
    """Abstract payment method interface."""

    @abstractmethod
    def processPayment(self, amount: float) -> bool:
        pass


class CardPaymentStrategy(PaymentStrategy):
    """Concrete strategy for card-based payments."""

    def processPayment(self, amount: float) -> bool:
        print(f"Card Payment processed for amount: {amount}")
        return True


class PaymentProcessor:
    """Delegates payment to the configured strategy."""

    def __init__(self, payment_strategy: PaymentStrategy):
        self.payment_strategy = payment_strategy

    def processPayment(self, amount: float) -> bool:
        return self.payment_strategy.processPayment(amount)


class BookingService:
    """Orchestrates lock → pay → confirm flow for seat bookings."""

    def __init__(self, lock_service: LockService, payment_processor: PaymentProcessor):
        self.lock_service = lock_service
        self.payment_processor = payment_processor
        self._next_booking_id: int = 1

    def bookSeats(self, show: Show, seats: List[ShowSeat], user: User) -> Booking:
        """Lock seats, process payment, and confirm booking atomically."""
        lock_status, conflicting_seat = self.lock_service.lockSeats(
            show_id=show.id,
            seats=seats,
            user_id=user.id,
        )

        if not lock_status:
            raise ValueError(
                f"Seat {conflicting_seat.seat.number} is unavailable or already locked"
            )

        amount = sum(seat.seat.base_price for seat in seats)

        try:
            if not self.payment_processor.processPayment(amount=amount):
                raise ValueError("Payment failed")

            for seat in seats:
                seat.status = SeatStatus.BOOKED

            booking = Booking(
                id=self._next_booking_id,
                user=user,
                show=show,
                seats=seats,
                status=BookingStatus.CONFIRMED,
            )
            self._next_booking_id += 1
            return booking

        except Exception:
            self.lock_service.releaseSeats(
                show_id=show.id,
                seats=seats,
                user_id=user.id,
            )
            raise

    # TODO: cancelBooking(booking, user) — set Booking.status=CANCELLED,
    #       reset ShowSeat.status=AVAILABLE, trigger refund via PaymentProcessor