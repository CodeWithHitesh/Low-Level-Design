# Chess Game — Low Level Design

## Problem Statement (as asked in interviews)

> Design a Chess Game for two players. The system should model the 8×8 board, all six piece types with their movement rules, turn-based play, move validation, and a win condition. Focus on clean OOP — piece hierarchy, movement validation, and game flow.

---

## Candidate Understanding (first 2–3 minutes)

- An 8×8 board made of `Cell` objects, each optionally holding a `Piece`.
- Six piece types — Rook, Knight, Bishop, Queen, King, Pawn — each with unique movement rules.
- Two players take **alternating turns**; a move is valid only if the piece belongs to the current player and obeys movement rules.
- A piece **cannot capture its own color**; path must be clear for sliding pieces (Rook, Bishop, Queen).
- Simplified win condition: **capturing the King** ends the game.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | Board setup with initial piece placement | `Board`, `Cell`, `PieceFactory` — **Singleton + Factory** |
| 2 | Piece hierarchy with movement rules | `Piece` (ABC) → `Rook`, `Knight`, `Bishop`, `Queen`, `King`, `Pawn` — **Template Method** |
| 3 | Path clearance for sliding pieces | `Rook._path_clear()`, `Bishop._check_path_clear()` |
| 4 | Move validation (own-piece check + piece rules) | `Piece.can_move()` → `_can_move()` (template skeleton) |
| 5 | Turn-based game flow with win detection | `Game.make_move()`, `GameState` enum |
| 6 | Console-based play loop | `Game.start()`, `console_move_provider()` |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** Check and checkmate detection
- **TODO:** Stalemate detection
- **TODO:** En passant and pawn promotion
- **TODO:** Castling (king + rook)
- **TODO:** Move history with undo/redo (Memento pattern)
- **TODO:** Observer pattern for game event notifications
- **TODO:** Player strategy — Human vs AI (Strategy pattern)

---

## Core Design Principles

| Principle | How It Applies |
|-----------|---------------|
| **SRP** | Each `Piece` subclass owns only its movement rule; `Game` owns turn flow; `Board` owns state |
| **OCP** | New piece types added via subclass + factory entry — no changes to `Game` or `Board` |
| **LSP** | Any `Piece` subclass is substitutable — `canMove` always works through the template method |
| **DIP** | `Game` depends on abstract `Piece.canMove()`, not specific piece implementations |

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Template Method** | `Piece.can_move()` calls `_can_move()` | Base class handles common checks (can't capture own piece); subclasses define specific movement rules |
| **Factory** | `PieceFactory.create()` | Centralized piece creation by name string; easy to extend |
| **Singleton** | `Board.__new__()` / `Board.getInstance()` | Ensures a single board instance throughout the game |

---

## Algorithmic Approach

### Template Method for move validation
`Piece.canMove()` handles the universal "can't capture own piece" check, then delegates to `_canMove()` for piece-specific geometry. This avoids duplicating the self-capture check in every subclass.

### Path clearance for sliding pieces
Rook and Bishop iterate along their movement axis checking for blockers. Queen reuses Rook + Bishop logic via composition (`Rook(self.is_white)._canMove(...) or Bishop(...)`).

### Board as 2D array of Cells
O(1) random access by (row, col). Each Cell optionally holds a Piece reference, making move execution a simple pointer swap.

---

## Class Overview

```
Cell
    │  - row, col, piece
    │
Piece (ABC)  ◄── Rook / Knight / Bishop / Queen / King / Pawn
    │  - canMove(board, start, end)     [template — common checks]
    │  - _canMove(board, start, end)    [abstract — piece-specific rules]
    │
PieceFactory
    │  - create(piece_type, is_white)
    │
Board (Singleton)
    │  - grid[8][8] of Cell
    │  - _initializeBoard()
    │
Player
    │  - is_white, name
    │
GameState (Enum)  —  IN_PROGRESS / WHITE_WIN / BLACK_WIN / DRAW
    │
Move
    │  - start, end
    │
Game
    │  - isValidMove(move)
    │  - makeMove(start_row, start_col, end_row, end_col)
    │  - start(move_provider)
```

---

## Edge Cases & Validation

| Scenario | Guard |
|----------|-------|
| Move to same square | Piece-specific geometry rejects (diff=0) |
| Move off board | Bounds check in `Game.makeMove()` |
| Move opponent's piece | `piece.is_white != self.is_white_turn` check |
| Capture own piece | `Piece.canMove()` rejects before delegating |
| Blocked path (Rook/Bishop/Queen) | `_pathClear()` iterates intermediate squares |
| No piece on start square | `move.start.piece is None` → invalid |

---

## Complexity Summary

| Operation | Time | Space |
|-----------|------|-------|
| `canMove` (Knight/King/Pawn) | O(1) | O(1) |
| `canMove` (Rook/Bishop/Queen) | O(n) n ≤ 7 path length | O(1) |
| `makeMove` | O(1) + `canMove` cost | O(1) |
| `_initializeBoard` | O(64) | O(64) cells |

---

## Extensibility

- **Check / Checkmate detection**: Add `isInCheck(color)` scanning all opponent pieces' `canMove` against the King's cell.
- **Castling**: Track `has_moved` on King/Rook; add special-case in `King._canMove()`.
- **En passant**: Track last move's double-pawn advance; add capture condition in `Pawn._canMove()`.
- **Move history + Undo**: Memento pattern storing (start, end, captured_piece) per move.
- **AI player**: Strategy pattern — `PlayerStrategy` with `HumanStrategy` and `MinimaxStrategy`.

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — confirm piece types, no check/checkmate, simplified king-capture win.
2. **Identify** classes top-down (3 min) — Cell, Piece hierarchy, Board, Game.
3. **Code** core classes in order (35 min):
   - Cell → Piece (ABC with template `can_move`) → Subclasses (Rook, Knight, Bishop, Queen, King, Pawn) → PieceFactory → Board (Singleton + `initialize_board`) → Game (validate + move + turn flow)
4. **Mention** TODO features verbally (2 min) — check/checkmate, castling, en passant, Memento for undo.
5. **Dry-run** a move end-to-end (3 min) — e.g. white pawn e2→e4, then black knight b8→c6.
