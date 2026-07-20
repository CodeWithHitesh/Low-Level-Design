# Parking Lot — Low Level Design

## Problem Statement

> Design a parking lot management system that supports multiple floors, typed parking slots, vehicle entry and exit, ticket issuance, duration-based fee calculation, and pluggable payment methods.

---

## Candidate Understanding (first 2–3 minutes)

- The lot is organised as **ParkingLot -> ParkingFloor -> ParkingSlot**.
- Each slot is typed for exactly one vehicle category, and only a matching vehicle can occupy it.
- Vehicle entry issues a **Ticket** containing the slot, vehicle, and entry timestamp.
- Vehicle exit validates an active ticket, computes a rounded-up hourly fee, processes payment, records exit time, and frees the slot.
- Pricing and payment are both pluggable via **Strategy** interfaces.
- The current implementation is **thread-safe at the lot level** using a single lock around shared mutable state.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Class / Mechanism |
|---|---------|----------------------|
| 1 | Multi-floor lot with typed slots | `ParkingLot`, `ParkingFloor`, `ParkingSlot` |
| 2 | Vehicle hierarchy with factory creation | `Vehicle`, `Car`, `Bike`, `VehicleFactory` |
| 3 | Ticket issuance on entry | `Ticket`, `ParkingLot.parkVehicle` |
| 4 | Active-ticket validation on exit | `ParkingLot._getActiveTicket` |
| 5 | Rounded-up hourly fee calculation | `ParkingLot._calculateDurationHours` + `ParkingFeeStrategy` |
| 6 | Basic and premium pricing models | `BasicHourlyFeeStrategy`, `PremiumHourlyFeeStrategy` |
| 7 | Payment processing abstraction | `PaymentStrategy`, `Payment`, `PaymentProcessor` |
| 8 | Thread-safe slot allocation and ticket lifecycle | `threading.Lock` in `ParkingLot` |

### TODO Features (mention but don't code)

- **TODO:** Display board that tracks available slots per floor and per type.
- **TODO:** Reservation / advance booking support.
- **TODO:** Additional vehicle categories such as truck or EV charging bays.
- **TODO:** Time-of-day or weekday surge pricing beyond the current premium multiplier model.
- **TODO:** Gate actors, attendants, and receipt persistence.

---

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | `ParkingSlot` manages occupancy, `Ticket` carries lifecycle data, `PaymentProcessor` coordinates payment, and fee strategies compute pricing. |
| **OCP** | New vehicle types, fee strategies, or payment methods are added as new classes without changing the orchestration flow. |
| **DIP** | `Vehicle` depends on the `ParkingFeeStrategy` abstraction, and payment orchestration depends on `PaymentStrategy` instead of concrete payment classes. |
| **Composition over Inheritance** | The structural model is composed as lot -> floors -> slots rather than a deep inheritance tree. |
| **Thread Safety** | Shared mutable state such as slot allocation, active tickets, and ticket ID generation is guarded by a single `threading.Lock`. |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `ParkingFeeStrategy`, `PaymentStrategy` | Allows runtime swapping of pricing rules and payment methods without condition-heavy orchestration code. |
| **Factory** | `VehicleFactory.create` | Centralises vehicle creation and keeps the rest of the code independent of concrete constructors. |
| **Composition** | `ParkingLot` -> `ParkingFloor` -> `ParkingSlot` | Mirrors the physical hierarchy and keeps responsibilities local to each layer. |
| **Dataclass** | `Ticket`, `ParkingSlot`, `ParkingFloor`, `ParkingLot`, `Vehicle` | Reduces boilerplate for data-heavy domain objects while preserving explicit fields. |

---

## Algorithmic Approach

### Slot allocation

`ParkingLot.findAvailableSlot(vehicle_type)` scans floors in order, and each floor performs a linear scan over its slots until it finds the first unoccupied slot of the requested type.

This gives deterministic first-fit behaviour and keeps the implementation interview-friendly:

- Per floor lookup: O(s), where `s` is slots on that floor
- Full lot lookup: O(f x s), where `f` is number of floors

For production scale, this could be replaced with a per-type free-slot index.

### Fee calculation

The lot computes parked duration as:

- `exit_time - entry_time`
- convert seconds to hours
- round up using `ceil`
- enforce a minimum billable duration of 1 hour

The resulting integer hour count is then delegated to the vehicle's fee strategy. This cleanly separates **duration computation** from **pricing policy**.

### Exit flow and lock scope

The exit flow is intentionally split into two lock regions:

1. Acquire lock and validate the ticket.
2. Compute the payable amount while state is stable.
3. Release the lock before calling payment, because payment is I/O-like work.
4. Reacquire the lock to record `exit_time`, free the slot, and remove the active ticket.

This keeps the critical section small and avoids blocking unrelated parking operations during payment processing.

---

## Class Overview

```
VehicleType (Enum)
├── CAR
└── BIKE

ParkingFeeStrategy (ABC)
├── calculateFee(vehicle, duration_hours) -> float
├── BasicHourlyFeeStrategy
└── PremiumHourlyFeeStrategy(multiplier=1.5)

Vehicle (ABC dataclass)
├── license_plate: str
├── vehicle_type: VehicleType
├── fee_strategy: ParkingFeeStrategy
├── base_rate: float
└── calculateFee(duration_hours) -> float
    ├── Car(base_rate=10)
    └── Bike(base_rate=5)

VehicleFactory
└── create(license_plate, vehicle_type, fee_strategy) -> Vehicle

PaymentStrategy (ABC)
├── processPayment(amount) -> bool
├── CreditCardPayment
└── CashPayment

Payment (dataclass)
├── amount: float
├── payment_strategy: PaymentStrategy
└── processPayment() -> bool

PaymentProcessor
└── process(amount, payment_strategy) -> None

ParkingSlot (dataclass)
├── spot_number: int
├── slot_type: VehicleType
├── vehicle: Optional[Vehicle]
├── parkVehicle(vehicle) -> None
├── vacateSlot() -> None
└── isOccupied() -> bool

ParkingFloor (dataclass)
├── floor_number: int
├── parking_slots: List[ParkingSlot]
└── findAvailableSlot(vehicle_type) -> Optional[ParkingSlot]

Ticket (dataclass)
├── ticket_id: int
├── vehicle: Vehicle
├── slot: ParkingSlot
├── entry_time: datetime
├── exit_time: Optional[datetime]
└── amount: Optional[float]

ParkingLot (dataclass)
├── parking_floors: List[ParkingFloor]
├── active_tickets: Dict[int, Ticket]
├── next_ticket_id: int
├── payment_processor: PaymentProcessor
├── lock: threading.Lock
├── findAvailableSlot(vehicle_type) -> Optional[ParkingSlot]
├── parkVehicle(vehicle) -> Ticket
├── exitVehicle(ticket, payment_strategy) -> None
├── _getActiveTicket(ticket) -> Ticket
├── _calculateDurationHours(entry_time, exit_time=None) -> int
└── _calculateParkingFee(ticket) -> float
```

---

## Edge Cases & Validation

| Scenario | Behaviour |
|----------|-----------|
| Unknown vehicle type in factory | `VehicleFactory.create` raises `ValueError` |
| Non-positive parking duration supplied to a fee strategy | Strategy raises `ValueError` |
| Premium multiplier less than or equal to 1 | `PremiumHourlyFeeStrategy` raises `ValueError` |
| Trying to park in an occupied slot | `ParkingSlot.parkVehicle` raises `ValueError` |
| Trying to park a vehicle in the wrong slot type | `ParkingSlot.parkVehicle` raises `ValueError` |
| No free slot for the vehicle type | `ParkingLot.parkVehicle` raises `ValueError` |
| Invalid or already-consumed ticket on exit | `ParkingLot._getActiveTicket` raises `ValueError` |
| Exit time earlier than entry time | `_calculateDurationHours` raises `ValueError` |
| Payment amount less than or equal to zero | `Payment.processPayment` raises `ValueError` |

### Why `Ticket` is part of the current design

The earlier conceptual version treated ticketing as an extension, but the current implementation already uses tickets as the core lifecycle object:

- Entry returns a `Ticket`
- Exit requires that ticket
- Active tickets live in `ParkingLot.active_tickets`
- Exit mutates the ticket with `amount` and `exit_time`

So ticketing is no longer a future enhancement; it is part of the implemented design.

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `ParkingFloor.findAvailableSlot` | O(s) | O(1) |
| `ParkingLot.findAvailableSlot` | O(f x s) | O(1) |
| `ParkingLot.parkVehicle` | O(f x s) | O(1) additional, excluding stored ticket |
| `_getActiveTicket` | O(1) | O(1) |
| `_calculateDurationHours` | O(1) | O(1) |
| `_calculateParkingFee` | O(1) | O(1) |
| `ParkingLot.exitVehicle` | O(1) plus payment side effect after ticket lookup | O(1) |

Overall live state is O(t + f x s), where `t` is the number of active tickets.

---

## Extensibility

- **New vehicle types**: add a new `VehicleType`, a concrete `Vehicle` subclass, and a factory mapping entry.
- **Richer pricing**: add strategies for weekend pricing, surge pricing, EV charging fees, or membership discounts.
- **Faster slot lookup**: maintain free-slot buckets per vehicle type on each floor to reduce allocation from linear scan to near O(1).
- **Reservation support**: introduce a reservation entity and a temporary hold state on slots.
- **Display board**: expose floor-level counts and update them whenever a slot is occupied or vacated.
- **Audit and receipts**: persist completed tickets and payment outcomes after exit instead of deleting them from active memory only.
- **Finer-grained concurrency**: replace the single lot lock with floor-level or slot-level coordination if contention becomes a bottleneck.
