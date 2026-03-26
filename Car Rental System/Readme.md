# Car Rental System — Low Level Design

## Problem Statement (as asked in interviews)

> Design a Car Rental System where users can rent vehicles from rental stores. Each store has an inventory of different vehicle types. Users should be able to check vehicle availability for a date range, make reservations, and pay for the rental. The system should prevent double-booking and support multiple payment methods.

---

## Candidate Understanding (first 2–3 minutes)

- Multiple **rental stores**, each at a different location, each with its own fleet of vehicles.
- Vehicles have **types** (Economy, Luxury, Bike, etc.) with different pricing multipliers.
- A user picks a **store → date range → vehicle**, and the system checks **availability** (no overlapping confirmed reservations, not under maintenance).
- On confirmation a **Reservation** is created; payment is processed via a chosen **payment method** (Cash / Card).
- **Observers** (e.g. the user) are notified on key events.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | Vehicle hierarchy with type-based pricing | `Vehicle` (ABC), `EconomyVehicle`, `LuxuryVehicle`, `Bike` — **Inheritance** |
| 2 | Availability check (date-overlap + maintenance) | `Vehicle.isAvailable()`, `Reservation.overlaps()` |
| 3 | Rental store inventory management | `RentalStore` — add / remove / list available vehicles |
| 4 | Reservation creation with conflict prevention | `ReservationManager` — validates availability before booking |
| 5 | Payment processing with multiple methods | `PaymentStrategy` (ABC), `CashPayment`, `CardPayment` — **Strategy Pattern** |
| 6 | Vehicle creation without exposing concrete classes | `VehicleFactory` — **Factory Pattern** |
| 7 | Notification on booking events | `Observer` (ABC), `UserObserver` — **Observer Pattern** |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** Search vehicles across multiple stores by city, vehicle type, date range
- **TODO:** Cancel reservation with refund logic
- **TODO:** Modify reservation (reschedule to new dates)
- **TODO:** Add locking per vehicle in `makeReservation` for thread-safety under concurrent requests

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `PaymentProcessor` + `PaymentStrategy` | Swap payment methods at runtime without changing processor logic |
| **Factory** | `VehicleFactory.create_vehicle()` | Decouple vehicle creation from client code; easy to add new types |
| **Observer** | `Observer` / `UserObserver` on `RentalSystem` | Notify interested parties (user, admin) on reservation events |
| **Singleton** | `RentalSystem.get_instance()` | Single global entry point; prevents multiple inconsistent system instances |

---

## Class Overview

```
VehicleType (Enum)          VehicleStatus (Enum)        ReservationStatus (Enum)
    │                            │                            │
    ▼                            ▼                            ▼
Vehicle (ABC)  ◄── EconomyVehicle / LuxuryVehicle / Bike
    │  - isAvailable(startDate, endDate)
    │  - calculateRent(days)  [abstract]
    │
    ├── reservations: List[Reservation]
    │
Reservation
    │  - overlaps(startDate, endDate)
    │
RentalStore
    │  - vehicles[]
    │  - getAvailableVehicles / addVehicle / removeVehicle
    │
ReservationManager
    │  - makeReservation(user, vehicle, startDate, endDate)
    │
PaymentStrategy (ABC) ◄── CashPayment / CardPayment
    │
PaymentProcessor  ─── uses strategy at runtime
    │
Observer (ABC) ◄── UserObserver
    │
RentalSystem  ─── orchestrates stores, factory, reservations, payments, observers
```

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — confirm multi-store, date-range booking, payment methods.
2. **Identify** classes & relationships top-down (3 min) — draw the class overview above.
3. **Code** core classes in order (35 min):
   - Enums → Vehicle hierarchy → Reservation → RentalStore → ReservationManager → Payment (Strategy) → Observer → RentalSystem
4. **Mention** TODO features verbally (2 min) — shows breadth of thinking.
5. **Dry-run** a booking flow end-to-end (3 min).