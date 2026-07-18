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

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | `Board` owns grid state; `MoveSnake` owns movement logic; `Game` owns the loop; `Player` owns input |
| **OCP** | New movement behaviors (e.g., power-ups) via `MoveSnake` subclass; new input sources via `PlayerStrategy` subclass |
| **DIP** | `Game` depends on abstract `PlayerStrategy`, not concrete `HumanPlayerStrategy` |
| **Template Method** | `MoveSnake.move()` defines the skeleton; subclasses vary only the tail behavior |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Template Method** | `MoveSnake.move()` → `_move()` | Common logic (add head, mark cell) in base; subclasses decide whether to remove tail (empty) or keep it (fruit) |
| **Strategy** | `PlayerStrategy` / `HumanPlayerStrategy` | Swap input source (human, AI) without changing game logic |
| **Factory** | `PlayerFactory.create()` | Create player with the right strategy by type string |

---

## Algorithmic Approach

### Snake as a deque
Head is `snake[0]`, tail is `snake[-1]`. Move = appendleft(new_head). On empty cell: pop tail (O(1)). On fruit: keep tail (snake grows). Deque gives O(1) at both ends.

### Collision detection
- **Wall collision**: `new_head_x < 0 or new_head_x >= rows` → game over (vertical boundary). Horizontal wraps via modulo.
- **Self collision**: Check if new head position is already in snake body (`CellValues.SNAKE` on grid).

### Fruit spawning
`spawnNewFruit()` picks a random empty cell. O(1) amortised when the grid is mostly empty; worst-case O(n×m) if nearly full.

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

## Edge Cases & Validation

| Scenario | Guard |
|----------|-------|
| Snake hits top/bottom wall | `new_head_x` out of bounds → `GAME_OVER` |
| Snake hits itself | Grid cell is `SNAKE` → `GAME_OVER` |
| Horizontal wrap-around | `new_head_y % cols` — wraps from right edge to left |
| Invalid direction input | `HumanPlayerStrategy` catches `KeyError`, re-prompts |
| Grid full (no empty cells for fruit) | Edge case for `spawnNewFruit` — game effectively won |

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| Move snake (empty cell) | O(1) appendleft + pop | O(1) |
| Move snake (fruit cell) | O(1) appendleft only | O(1) |
| Collision check | O(1) grid lookup | O(1) |
| Spawn fruit | O(1) amortised (random probe) | O(1) |
| Display board | O(n×m) | O(1) |

---

## Extensibility

- **AI player**: `GreedyAIStrategy` using BFS/A* to find shortest path to fruit.
- **Power-ups**: New `CellValues` entry + `MoveSnakePowerUp` subclass handling the effect.
- **Speed progression**: `Game` decreases input timeout as score increases.
- **Multiplayer**: Multiple snakes on same board; collision between snakes = game over for the collider.
- **Observer for UI**: Decouple rendering from `Board.display()` — push state to GUI/web frontend.

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — grid size, single player, no score persistence, terminal-based.
2. **Identify** classes top-down (3 min) — Board (grid + snake), MoveSnake hierarchy, Player + Strategy, Game.
3. **Code** core classes in order (35 min):
   - Enums → MoveSnake template hierarchy → Board (init + move + display) → Direction → PlayerStrategy + HumanPlayerStrategy → PlayerFactory → Game loop
4. **Mention** TODO features verbally (2 min) — AI strategy, scoring, Observer for UI.
5. **Dry-run** a few moves (3 min) — snake moves right, eats fruit (grows), moves up, hits boundary (game over).
