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

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `PlayerStrategy` / `HumanPlayerStrategy` | Swap input source (human, AI) without touching game logic |
| **Factory** | `PlayerFactory.create_player()` | Centralized player creation by type string; easy to add AI types |
| **Observer** | `GameObserver` / `ConsoleDisplayObserver` | Decouple display/logging from game flow; notify on move and state change |

---

## Class Overview

```
Symbol (Enum)  —  X / O / EMPTY
State (Enum)   —  IN_PROGRESS / X_WIN / O_WIN / DRAW

PlayerStrategy (ABC)  ◄── HumanPlayerStrategy
    │  - make_move(board) → (row, col)
    │
Player
    │  - name, symbol, strategy
    │
PlayerFactory
    │  - create_player(player_type, name, symbol)
    │
Board
    │  - grid[N][N]
    │  - is_valid_move(), mark_cell()
    │  - check_winner(symbol), display()
    │
GameObserver (ABC)  ◄── ConsoleDisplayObserver
    │  - on_move_made(player, row, col)
    │  - on_game_state_changed(state, winner)
    │
Game
    │  - players[], board, current_turn, current_state
    │  - register_observer(), notify_move(), notify_game_state_changed()
    │  - play()  [main loop]
    │  - reset_game()
```

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — board size, two human players, no AI, no undo.
2. **Identify** classes top-down (3 min) — Board, Player + Strategy, Observer, Game.
3. **Code** core classes in order (35 min):
   - Enums → PlayerStrategy + HumanPlayerStrategy → Player → PlayerFactory → Board (validate, mark, check_winner, display) → GameObserver + ConsoleDisplayObserver → Game (turn loop, state transitions, observer hooks, reset)
4. **Mention** TODO features verbally (2 min) — AI strategy, undo (Memento), online multiplayer.
5. **Dry-run** a short game (3 min) — X plays (0,0), O plays (1,1), X plays (0,1), O plays (1,0), X plays (0,2) → X wins row 0.
