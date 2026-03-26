# Low-Level Design — Interview Prep

A collection of classic LLD problems solved in Python, scoped for a **45-minute interview round**. Each folder contains a `design.py` with the implementation and (where available) a `Readme.md` with the problem description, scope, and patterns used.

---

## Problems

| # | Problem | Patterns Used |
|---|---------|---------------|
| 1 | [Car Rental System](Car%20Rental%20System/) | Strategy, Factory, Observer, Singleton |
| 2 | [Parking Lot](Parking%20Lot/) | Strategy (fee + payment), Factory, Composition |
| 3 | [Chess Game](Chess%20Game/) | Template Method, Factory, Singleton |
| 4 | [Elevator](Elevator/) | Strategy (scheduling), Observer |
| 5 | [Snake and Food Game](Snake%20and%20Food%20Game/) | Template Method, Strategy, Factory |
| 6 | [Tic Tac Toe Game](Tic%20Tac%20Toe%20Game/) | Strategy, Factory, Observer |

---

## Common Design Patterns Across Problems

| Pattern | Where It Appears |
|---------|-----------------|
| **Strategy** | Payment methods (Car Rental, Parking Lot), player input (Snake, Tic Tac Toe), elevator scheduling |
| **Factory** | Vehicle creation (Car Rental, Parking Lot), piece creation (Chess), player creation (Snake, Tic Tac Toe) |
| **Observer** | Booking notifications (Car Rental), floor display (Elevator), game state changes (Tic Tac Toe) |
| **Singleton** | System entry point (Car Rental), Board (Chess) |
| **Template Method** | Piece movement validation (Chess), snake move handling (Snake) |

---

## How to Use

1. Pick a problem and read its `Readme.md` (if available) for scope and interview strategy.
2. Open `design.py` — code is ordered top-down (enums → models → services → orchestrator).
3. Look for `# TODO:` comments — these mark features intentionally left out of scope for a 45-min round but worth mentioning verbally to the interviewer.
4. Practice explaining class relationships and pattern choices out loud — that's what interviewers evaluate.
