# Elevator System — Low Level Design

## Problem Statement (as asked in interviews)

> Design an Elevator System for a building with multiple floors and multiple elevators. The system should handle floor requests, move elevators in the correct direction, notify displays on floor/state changes, and support pluggable scheduling strategies. Focus on class structure, state management, and extensibility.

---

## Candidate Understanding (first 2–3 minutes)

- A **Building** has N floors and an **ElevatorController** managing multiple **Elevators**.
- Each elevator tracks its current floor, direction (UP / DOWN / IDLE), and state (IDLE / MOVING / MAINTENANCE / STOPPED).
- Users make **ElevatorRequests** (floor + direction); the controller uses a **scheduling strategy** to assign the best elevator.
- **Observers** (e.g. floor displays) are notified on floor changes and state changes.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | Building, floor, and elevator modeling | `Building`, `Floor`, `Elevator` |
| 2 | Elevator state and direction tracking | `State` enum, `Direction` enum |
| 3 | Pluggable scheduling for elevator assignment | `SchedulingStrategy` (ABC), `FCFSStrategy` — **Strategy Pattern** |
| 4 | Observer notifications on floor/state changes | `ElevatorObserver` (ABC), `DisplayObserver` — **Observer Pattern** |
| 5 | Controller orchestration | `ElevatorController` — ties elevators, floors, and strategy together |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** Implement `FCFSStrategy.get_next_floor()` — actual FCFS scheduling logic
- **TODO:** `ElevatorRequest` with source floor, destination floor, and direction
- **TODO:** Elevator movement loop — process request queue, move floor-by-floor, notify observers
- **TODO:** Additional strategies — SCAN (elevator algorithm), LOOK, shortest-seek-time-first
- **TODO:** Door open/close with timeout
- **TODO:** Weight/capacity check before accepting passengers
- **TODO:** Emergency stop and maintenance mode transitions
- **TODO:** Thread-safety for concurrent requests from multiple floors

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `SchedulingStrategy` / `FCFSStrategy` | Swap scheduling algorithms without changing controller logic |
| **Observer** | `ElevatorObserver` / `DisplayObserver` | Decouple display updates from elevator movement logic |

---

## Class Overview

```
Direction (Enum)  —  IDLE / UP / DOWN
State (Enum)      —  IDLE / MOVING / MAINTENANCE / STOPPED

Floor
    │  - floor_number
    │
ElevatorRequest
    │  - (placeholder for source, destination, direction)
    │
ElevatorObserver (ABC)  ◄── DisplayObserver
    │  - onFloorChange(floor, elevator)
    │  - onStateChange(state, elevator)
    │
Elevator
    │  - id, current_floor, direction, state
    │  - observers[], requests[]
    │
SchedulingStrategy (ABC)  ◄── FCFSStrategy
    │  - get_next_floor(elevator)
    │
ElevatorController
    │  - elevators[], floors[], scheduling_strategy
    │
Building
    │  - name, elevator_controller, number_of_floors
```

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — number of elevators, scheduling expected, door mechanics in/out of scope.
2. **Identify** classes top-down (3 min) — Building → Controller → Elevator, Strategy, Observer.
3. **Code** core classes in order (35 min):
   - Enums → Floor → ElevatorRequest → ElevatorObserver + DisplayObserver → Elevator → SchedulingStrategy + FCFSStrategy → ElevatorController → Building
4. **Mention** TODO features verbally (2 min) — SCAN algorithm, weight limits, door timeout, concurrency.
5. **Dry-run** a request flow (3 min) — user on floor 3 presses UP → controller picks elevator → elevator moves → observer notifies display.

---

## Files

| File | Description |
|------|-------------|
| `design.py` | Interview-scoped implementation (core classes + patterns) |
| `real-design.py` | Extended implementation with more complete elevator logic |
