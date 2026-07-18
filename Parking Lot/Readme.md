# Parking Lot — Low Level Design

## Problem Statement

> Design a parking lot management system that handles vehicle entry/exit, slot allocation, fee calculation, and payment processing. Support multiple vehicle types, floors, and payment methods.

---

## Candidate Understanding (first 2–3 minutes)

- Multi-floor lot with **typed slots** (Car slots, Bike slots) — vehicles can only park in matching slot types.
- On entry: find an available matching slot → issue a ticket → mark slot occupied.
- On exit: calculate fee based on duration + vehicle type → process payment → free the slot.
- Different **fee strategies** (hourly, premium, surge) and **payment methods** (cash, card) are pluggable.
- No double-parking: a slot either has a vehicle or doesn't.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes |
|---|---------|-------------|
| 1 | Multi-floor slot model | `ParkingLot` → `ParkingFloor` → `ParkingSlot` |
| 2 | Vehicle type hierarchy | `Vehicle` (ABC) → `Car`, `Bike` |
| 3 | Slot allocation by vehicle type | `ParkingFloor.findAvailableSlot()` |
| 4 | Fee calculation (Strategy) | `ParkingFeeStrategy` → `BasicHourlyFeeStrategy` |
| 5 | Payment processing (Strategy) | `PaymentStrategy` → `CreditCardPayment`, `CashPayment` |
| 6 | Vehicle creation | `VehicleFactory` |

### TODO Features (mention but don't code)

- **TODO:** Parking ticket with entry/exit timestamps
- **TODO:** Entry/exit gate orchestration
- **TODO:** Display board (Observer pattern) showing available slots per floor
- **TODO:** Reservation system for pre-booking slots
- **TODO:** Surge pricing / time-of-day pricing

---

## Core Design Principles

| Principle | How It Applies |
|---|---|
| **SRP** (Single Responsibility) | Each class owns one job — `ParkingSlot` manages occupancy, `Payment` handles transactions, `ParkingFeeStrategy` computes fees. |
| **OCP** (Open/Closed) | New fee strategies or payment methods are added by creating a new class, not modifying existing ones. |
| **DIP** (Dependency Inversion) | `Vehicle` depends on `ParkingFeeStrategy` abstraction, not a concrete fee class. Same for `Payment` → `PaymentStrategy`. |
| **Composition over Inheritance** | `ParkingLot` → `ParkingFloor` → `ParkingSlot` hierarchy is built via composition, not deep inheritance trees. |

---

## Design Patterns Used

| Pattern | Where | Why |
|---|---|---|
| **Strategy** | `ParkingFeeStrategy`, `PaymentStrategy` | Swap fee algorithms or payment methods at runtime without touching existing code. |
| **Factory** | `VehicleFactory` | Centralises object creation; easy to extend when new vehicle types are added. |
| **Composition** | `ParkingLot` → `ParkingFloor` → `ParkingSlot` | Models the real-world containment hierarchy cleanly. |

---

## Class Overview

```
ParkingLot
├── parkingFloors: List[ParkingFloor]
├── parkVehicle(vehicle)
└── vacateSlot(slot, vehicle)

ParkingFloor
├── floorNumber, parkingSlots: List[ParkingSlot]
└── findAvailableSlot(vehicleType) → ParkingSlot | None

ParkingSlot
├── spotNumber, slotType, vehicle, isOccupied
├── parkVehicle(vehicle)
└── vacateSlot()

Vehicle (ABC)
├── licensePlate, vehicleType, feeStrategy
└── calculateFee(duration, durationType) → float   [abstract]
    ├── Car
    └── Bike

VehicleFactory.createVehicle(plate, type, feeStrategy) → Vehicle

ParkingFeeStrategy (ABC)          PaymentStrategy (ABC)
├── BasicHourlyFeeStrategy        ├── CreditCardPayment
└── PremiumHourlyFeeStrategy      └── CashPayment

Payment
├── amount, paymentStrategy
└── processPayment() → bool
```

---

## Algorithmic Approach

### Slot allocation — linear scan
`ParkingFloor.findAvailableSlot(vehicleType)` iterates slots looking for the first unoccupied slot matching the vehicle type. O(s) per floor. For interview scope this is sufficient; production systems would use a free-list or bitmap per type.

### Fee calculation — Strategy delegation
`Vehicle.calculateFee(duration, durationType)` delegates to its `fee_strategy`. This avoids conditionals in the vehicle class and makes adding pricing tiers trivial.

### Why composition (Lot → Floor → Slot)?
Models the real physical hierarchy. Each layer owns its own responsibility: Lot routes to floors, Floor owns slots, Slot tracks occupancy. No deep inheritance trees needed.

---

## Edge Cases & Validation

| Scenario | Guard |
|----------|-------|
| No available slot for vehicle type | `findAvailableSlot` returns None → caller handles |
| Park in occupied slot | `parkVehicle` raises `ValueError` if `is_occupied` |
| Vacate already-empty slot | `vacateSlot` checks occupancy before clearing |
| Payment amount ≤ 0 | `Payment.processPayment()` raises `ValueError` |
| Unknown vehicle type in factory | `VehicleFactory` raises `ValueError` |

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `findAvailableSlot` (per floor) | O(s) s = slots on floor | O(1) |
| `parkVehicle` (full lot) | O(f × s) f = floors | O(1) |
| `vacateSlot` | O(1) | O(1) |
| `calculateFee` | O(1) | O(1) |
| `processPayment` | O(1) | O(1) |

---

## Extensibility (Verbal Discussion Points)

These can be **mentioned in the interview** as extensions without implementing them:

- **New vehicle types** (Truck, EV) → add to `VehicleType` enum; slots already match by type.
- **Surge / premium pricing** → new `ParkingFeeStrategy` subclass (e.g., `PremiumHourlyFeeStrategy`).
- **Composite pattern** → `ParkingLot.isFull()` checks if all floors are full; each floor checks its slots. Recursive composite structure.
- **Parking ticket** → `ParkingTicket` class with `ticketId`, `vehicle`, `slot`, `entryTime`. Integrates with `ParkingLot.parkVehicle()` to issue on entry and validate on exit.
- **Entry / exit gates** → `Gate` class that orchestrates ticket issuance and payment validation.
- **Display board** → observer pattern; notifies available slot counts per floor.
- **Reservation system** → `ReservationManager` that pre-allocates slots before arrival.
- **UPI / wallet payments** → new `PaymentStrategy` subclass, zero changes to `Payment` class.
