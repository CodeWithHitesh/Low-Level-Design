# Low-Level Design — Interview Prep

A collection of classic LLD problems solved in Python, scoped for a **45-minute interview round**. Each folder contains a `design.py` with the implementation and a `Readme.md` with the problem description, scope, and patterns used.

---

## Problems

| # | Problem | Patterns Used |
|---|---------|---------------|
| 1 | [Car Rental System](Car%20Rental%20System/) | Strategy, Factory, Observer, Singleton |
| 2 | [Parking Lot](Parking%20Lot/) | Strategy (fee + payment), Factory, Composition |
| 3 | [Chess Game](Chess%20Game/) | Template Method, Factory, Singleton |
| 4 | [Elevator](Elevator/) | Strategy (scheduling), Observer, Command |
| 5 | [Snake and Food Game](Snake%20and%20Food%20Game/) | Template Method, Strategy, Factory |
| 6 | [Tic Tac Toe Game](Tic%20Tac%20Toe%20Game/) | Strategy, Factory, Observer |
| 7 | [File System](File%20System/) | Composite, Singleton |
| 8 | [Rate Limiter](Rate%20Limiter/) | Strategy, Factory |
| 9 | [Splitwise](Splitwise/) | Strategy, Factory, Observer |
| 10 | [Web Socket](Web%20Socket/) | *(System Design concept — async I/O demo)* |
| 11 | [Resource Lease System](Resource%20Lease%20System/) | FIFO Deque, Lazy Deletion, Thread Safety |

---

## Design Patterns

| # | Pattern | Folder |
|---|---------|--------|
| 1 | [Singleton Pattern](Design%20Patterns/Singleton%20Pattern/) | Explanation + code examples |

---

## Common Design Patterns Across Problems

| Pattern | Where It Appears |
|---------|-----------------|
| **Strategy** | Payment methods (Car Rental, Parking Lot), player input (Snake, Tic Tac Toe), elevator scheduling, rate limiter algorithms, expense splitting (Splitwise) |
| **Factory** | Vehicle creation (Car Rental, Parking Lot), piece creation (Chess), player creation (Snake, Tic Tac Toe), rate limiter creation |
| **Observer** | Booking notifications (Car Rental), floor display (Elevator), game state changes (Tic Tac Toe), balance updates (Splitwise) |
| **Singleton** | System entry point (Car Rental), Board (Chess), FileSystem |
| **Template Method** | Piece movement validation (Chess), snake move handling (Snake) |
| **Composite** | File/Directory hierarchy (File System) |
| **Command** | Elevator requests (Elevator) |
| **FIFO Deque + Lazy Deletion** | O(1) amortised token expiry (Resource Lease System) |
| **Threading Lock** | Thread-safe token grant / release (Resource Lease System, Rate Limiter) |

---

## How to Use

1. Pick a problem and read its `Readme.md` for scope and interview strategy.
2. Open `design.py` — code is ordered top-down (enums → models → services → orchestrator).
3. Look for `# TODO:` comments — these mark features intentionally left out of scope for a 45-min round but worth mentioning verbally to the interviewer.
4. Practice explaining class relationships and pattern choices out loud — that's what interviewers evaluate.
