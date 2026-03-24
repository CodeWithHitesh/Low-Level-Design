# Parking Lot — Low Level Design

## Problem Statement

Design a parking lot management system that handles vehicle entry/exit, slot allocation, fee calculation, and payment processing.

---

## Requirements

### Setup
- The parking lot has **multiple floors**, each with multiple slots.
- Different vehicle types (**Bike, Car**) occupy matching slot types.
- A **parking ticket** is issued on entry, linking a vehicle to an assigned slot.
- The system calculates the **parking fee** based on duration and vehicle type.

### Exit & Payment
- A vehicle must **complete payment** before exiting.
- Multiple payment methods (**Cash, Credit Card**) are supported via a strategy interface.
- On successful payment, the slot is freed and the ticket invalidated.

### Constraints
- A vehicle **cannot** park in an already occupied slot.
- A vehicle **cannot** exit without a valid ticket and completed payment.

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
