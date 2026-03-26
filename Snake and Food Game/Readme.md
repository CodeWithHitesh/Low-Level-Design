# Snake and Food Game — Low Level Design

## Problem Statement (as asked in interviews)

> Design a Snake Game on a grid board. The snake moves in a direction chosen by the player, grows when it eats fruit, and dies if it hits a boundary or itself. The board spawns fruits randomly. Focus on clean separation of board logic, movement handling, player input, and game flow.

---

## Candidate Understanding (first 2–3 minutes)

- A **Board** (N×M grid) contains cells that are EMPTY, FRUIT, or SNAKE.
- The **snake** is a `deque` — head at front, tail at back. Movement = add new head, remove tail (or keep tail if eating fruit).
- **Fruits** are randomly spawned at initialization and re-spawned after consumption.
- **Game over** on: hitting a vertical boundary, or the snake colliding with itself.
- Player input determines direction (UP / DOWN / LEFT / RIGHT).

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | Grid board with cell states | `Board`, `CellValues` enum |
| 2 | Snake initialization and movement | `Board.init_snake()`, `Board.move_snake()` using `deque` |
| 3 | Fruit spawning and re-spawning | `Board.init_fruits()`, `Board.spawn_new_fruit()` |
| 4 | Move handling — grow vs slide | `MoveSnake` (ABC) → `MoveSnakeFruit`, `MoveSnakeEmpty` — **Template Method** |
| 5 | Player input with pluggable strategy | `PlayerStrategy` (ABC), `HumanPlayerStrategy` — **Strategy Pattern** |
| 6 | Player creation | `PlayerFactory` — **Factory Pattern** |
| 7 | Game loop with collision detection | `Game.play()` — boundary check, self-collision check, state transitions |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** AI player strategy (e.g. greedy shortest-path-to-fruit)
- **TODO:** Score tracking and high-score persistence
- **TODO:** Increasing difficulty (speed / fewer fruits over time)
- **TODO:** Observer for UI updates (decouple display from game loop)
- **TODO:** Horizontal boundary wrapping is implemented; vertical could be made configurable

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Template Method** | `MoveSnake.move()` → `_move()` | Common logic (add head, mark cell) in base; subclasses decide whether to remove tail (empty) or keep it (fruit) |
| **Strategy** | `PlayerStrategy` / `HumanPlayerStrategy` | Swap input source (human, AI) without changing game logic |
| **Factory** | `PlayerFactory.create()` | Create player with the right strategy by type string |

---

## Class Overview

```
CellValues (Enum)  —  EMPTY / FRUIT / SNAKE
Direction (Enum)   —  UP / DOWN / LEFT / RIGHT

MoveSnake (ABC)  ◄── MoveSnakeFruit / MoveSnakeEmpty
    │  - move(snake, pos_x, pos_y, board)   [template — add head]
    │  - _move(snake, board)                 [abstract — keep or remove tail]
    │
Board
    │  - grid[N][M], snake (deque)
    │  - init_snake(), init_fruits(), spawn_new_fruit()
    │  - move_snake(new_head_x, new_head_y, cellvalue)
    │  - display()
    │
PlayerStrategy (ABC)  ◄── HumanPlayerStrategy
    │  - make_move(board)
    │
Player
    │  - name, strategy
    │
PlayerFactory
    │  - create(name, player_type)
    │
GameState (Enum)  —  IN_PROGRESS / GAME_OVER
    │
Game
    │  - player, board, snake, grid
    │  - play()  [main loop — input → collision check → move → display]
```

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — grid size, single player, no score persistence, terminal-based.
2. **Identify** classes top-down (3 min) — Board (grid + snake), MoveSnake hierarchy, Player + Strategy, Game.
3. **Code** core classes in order (35 min):
   - Enums → MoveSnake template hierarchy → Board (init + move + display) → Direction → PlayerStrategy + HumanPlayerStrategy → PlayerFactory → Game loop
4. **Mention** TODO features verbally (2 min) — AI strategy, scoring, Observer for UI.
5. **Dry-run** a few moves (3 min) — snake moves right, eats fruit (grows), moves up, hits boundary (game over).
