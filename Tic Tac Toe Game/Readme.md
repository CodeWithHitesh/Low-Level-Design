# Tic Tac Toe Game — Low Level Design

## Problem Statement (as asked in interviews)

> Design a Tic-Tac-Toe game for two players on an N×N board (default 3×3). The system should handle player turns, move validation, win/draw detection (rows, columns, diagonals), and support pluggable player strategies and game event observers.

---

## Candidate Understanding (first 2–3 minutes)

- An N×N **Board** of cells, each EMPTY, X, or O.
- Two **Players** alternate turns; each uses a **strategy** to pick a move (human input, future AI).
- After every move the board checks for a **winner** (complete row, column, or diagonal) or a **draw** (no empty cells).
- **Observers** are notified on each move and on game-state changes (win / draw).
- The game supports **reset** without recreating players or observers.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | Board with move validation and display | `Board` — `is_valid_move()`, `mark_cell()`, `display()` |
| 2 | Win detection (rows, columns, diagonals) | `Board.check_winner()` |
| 3 | Draw detection | `Game.play()` — `remaining_cells == 0` check |
| 4 | Pluggable player input | `PlayerStrategy` (ABC), `HumanPlayerStrategy` — **Strategy Pattern** |
| 5 | Player creation by type | `PlayerFactory.create_player()` — **Factory Pattern** |
| 6 | Game event notifications | `GameObserver` (ABC), `ConsoleDisplayObserver` — **Observer Pattern** |
| 7 | Turn-based game loop with state transitions | `Game.play()`, `State` enum, `Game.reset_game()` |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** AI player strategy (random, minimax)
- **TODO:** Configurable board size beyond 3×3 with generalized win-length
- **TODO:** Online multiplayer with network-based player strategy
- **TODO:** Move history with undo/redo (Memento pattern)
- **TODO:** Tournament mode — best of N games

---

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | `Board` owns grid state and win detection; `Player` owns move delegation; `Game` owns turn flow |
| **OCP** | New player types (AI) via `PlayerStrategy` subclass; new observers via `GameObserver` subclass |
| **DIP** | `Game` depends on abstract `PlayerStrategy` and `GameObserver`, not concrete implementations |
| **Observer** | Display/logging decoupled from game loop; add new observers without changing `Game` |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `PlayerStrategy` / `HumanPlayerStrategy` | Swap input source (human, AI) without touching game logic |
| **Factory** | `PlayerFactory.create_player()` | Centralized player creation by type string; easy to add AI types |
| **Observer** | `GameObserver` / `ConsoleDisplayObserver` | Decouple display/logging from game flow; notify on move and state change |

---

## Algorithmic Approach

### Win detection
`Board.checkWinner(symbol)` checks all rows, columns, and both diagonals. O(n) per check (n = board size). Called once per move.

### Draw detection
Track `remaining_cells` counter. Decrement on each valid move. When it hits 0 without a winner → draw. O(1) check.

### Why Strategy for players?
Decouples input mechanism from game logic. `HumanPlayerStrategy` reads stdin; a future `MinimaxStrategy` would compute the optimal move. Game loop is identical either way.

---

## Class Overview

```
Symbol (Enum)  —  X / O / EMPTY
State (Enum)   —  IN_PROGRESS / X_WIN / O_WIN / DRAW

PlayerStrategy (ABC)  ◄── HumanPlayerStrategy
    │  - makeMove(board) → (row, col)
    │
Player
    │  - name, symbol, strategy
    │
PlayerFactory
    │  - createPlayer(player_type, name, symbol)
    │
Board
    │  - grid[N][N]
    │  - isValidMove(), markCell()
    │  - checkWinner(symbol), display()
    │
GameObserver (ABC)  ◄── ConsoleDisplayObserver
    │  - onMoveMade(player, row, col)
    │  - onGameStateChanged(state, winner)
    │
Game
    │  - players[], board, current_turn, current_state
    │  - registerObserver(), notifyMove(), notifyGameStateChanged()
    │  - play()  [main loop]
    │  - resetGame()
```

---

## Edge Cases & Validation

| Scenario | Guard |
|----------|-------|
| Move out of bounds | `isValidMove` checks `0 <= row < size` |
| Move on occupied cell | `isValidMove` checks `grid[row][col] == EMPTY` |
| Invalid input (non-integer) | `HumanPlayerStrategy` catches `ValueError`, re-prompts |
| Win on last possible move | Win check runs before draw check |
| Multiple observers | All notified in registration order |

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `markCell` | O(1) | O(1) |
| `checkWinner` | O(n) n = board size | O(1) |
| `isValidMove` | O(1) | O(1) |
| Full game (n×n board) | O(n²) moves × O(n) win check = O(n³) | O(n²) board |

---

## Extensibility

- **AI player (Minimax)**: New `MinimaxStrategy` implementing `PlayerStrategy` — zero changes to `Game`.
- **Larger boards**: Constructor accepts `size`; win detection already generalizes to n×n.
- **Custom win-length**: Add `win_length` param; modify `checkWinner` to check consecutive runs of that length.
- **Undo/Redo**: Memento pattern storing `(row, col, symbol)` per move; `Game.undo()` restores previous state.
- **Network play**: `NetworkPlayerStrategy` that sends/receives moves over a socket.

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — board size, two human players, no AI, no undo.
2. **Identify** classes top-down (3 min) — Board, Player + Strategy, Observer, Game.
3. **Code** core classes in order (35 min):
   - Enums → PlayerStrategy + HumanPlayerStrategy → Player → PlayerFactory → Board (validate, mark, check_winner, display) → GameObserver + ConsoleDisplayObserver → Game (turn loop, state transitions, observer hooks, reset)
4. **Mention** TODO features verbally (2 min) — AI strategy, undo (Memento), online multiplayer.
5. **Dry-run** a short game (3 min) — X plays (0,0), O plays (1,1), X plays (0,1), O plays (1,0), X plays (0,2) → X wins row 0.
