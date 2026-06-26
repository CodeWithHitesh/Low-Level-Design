# Copilot Agent Instructions — Low-Level Design

This repository is a curated set of interview-ready Python Low-Level Design (LLD) solutions. Each problem lives in its own folder with exactly two files: `design.py` and `Readme.md`.

## Folder Structure

```
Problem Name/
    design.py    ← implementation
    Readme.md    ← design rationale, class overview, complexity, edge cases
```

Never modify files outside the target problem's folder. `temp.py` at the root is a scratch file — ignore it.

## design.py Conventions

**File layout (top to bottom):**
1. Module docstring — names the design patterns and SOLID principles used
2. Imports — `abc`, `dataclasses`, `enum`, `typing`, then `collections` / `threading` / `time` if needed
3. Custom exceptions (if any) — optional; `ValueError` is sufficient for most interview rounds
4. Enums
5. Abstract base classes (ABCs)
6. Concrete implementations
7. `@dataclass` models
8. Factory classes (`@staticmethod create(...)`)
9. Orchestrator / service class
10. `if __name__ == "__main__":` demo block

**Style rules:**
- Docstrings on classes and non-trivial methods; no inline comments
- Full type hints on all method signatures
- Method names: camelCase (`calculateFee`, `parkVehicle`); params/fields: snake_case
- `@dataclass` for all data models; use `field(default_factory=...)` for mutable defaults
- Thread safety via per-entity `threading.Lock`; prefer `defaultdict(threading.Lock)` over a single global lock
- No `frozen=True` on dataclasses that have planned mutation (e.g., lease renewal, state updates)
- Raise `ValueError` for invalid constructor arguments and business rule violations

## Readme.md Conventions

Every Readme must contain these sections in order — see [Resource Lease System/Readme.md](Resource%20Lease%20System/Readme.md) or [Rate Limiter/Readme.md](Rate%20Limiter/Readme.md) as reference:

1. **Problem Statement** — quoted one-paragraph requirement
2. **Candidate Understanding** — bullet points, framed as "first 2–3 minutes"
3. **Scope for a 45-minute Round** — Core Features table + TODO Features list
4. **Core Design Principles** — table: Principle | How It Applies
5. **Design Patterns Used** — table: Pattern | Where | Why
6. **Algorithmic Approach** — justifies data structure choices with trade-offs (e.g., deque vs heap)
7. **Class Overview** — ASCII tree of classes, fields, and method signatures
8. **Edge Cases & Validation** — inputs that need guarding and why
9. **Complexity Summary** — table: Operation | Time | Space
10. **Extensibility** — verbal discussion points for follow-up interview questions

## General Design Principles

- **Validate inputs before acquiring any lock** — pure input validation needs no shared state; holding a lock for it wastes contention.
- **Prefer composition over deep inheritance** — use `List[Type]` containment and strategy objects rather than multi-level ABC trees.
- **Justify every data structure choice** — document why (e.g., deque vs heap, dict vs list) with explicit trade-offs in the Readme.
- **Collapse ambiguous error cases into one `ValueError`** — do not expose internal state (e.g., "not found" vs "not owned") through different error types.
- **Thread safety is per-entity** — use `defaultdict(threading.Lock)` rather than a single global lock to reduce contention.
- **No `frozen=True` on dataclasses that have planned mutation** — document the reason in the class docstring when omitting it.

## Adding a New Design Problem

1. Create `Problem Name/design.py` and `Problem Name/Readme.md`
2. Follow the file layout and section order above
3. Update the root [Readme.md](Readme.md) — add a row to the **Problems** table (increment `#`, link the folder, list patterns used) and add any new patterns to the **Common Design Patterns Across Problems** table
4. One problem per PR; branch name: `design/<topic>`
5. Do not touch any other folder
