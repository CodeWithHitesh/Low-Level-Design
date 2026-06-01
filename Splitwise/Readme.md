# Splitwise — Low Level Design

## Problem Statement (as asked in interviews)

> Design a simplified Splitwise-like expense sharing system. Users can create group expenses, split them equally or by percentage, track balances between users, and settle debts with minimum transactions.

---

## Candidate Understanding (first 2–3 minutes)

- **Users** can create expenses and split them among participants.
- Expenses support multiple **split strategies** (equal, percentage, exact amounts).
- A **BalanceSheet** tracks how much each user owes every other user (directed pairwise balances).
- The system can compute **simplified settlements** — minimum transactions to clear all debts.
- **Observers** are notified when expenses are added or updated.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | User management | `User`, `UserManager` |
| 2 | Pluggable expense splitting | `Split` (ABC), `EqualSplit`, `PercentageSplit` — **Strategy Pattern** |
| 3 | Split creation by type | `SplitFactory` — **Factory Pattern** |
| 4 | Expense creation with payer and participants | `Expense`, `ExpenseManager` |
| 5 | Balance tracking (pairwise debts) | `BalanceSheet`, `UserPair` |
| 6 | Notifications on expense events | `Observer` (ABC), `BalanceSheet` as observer — **Observer Pattern** |
| 7 | Simplified settlements (greedy) | `BalanceSheet.getSimplifiedSettlements()` |
| 8 | Optimal minimum settlements (backtracking + bitmask DP) | `BalanceSheet.getSubOptimalMinimumSettlements()`, `getOptimalMinimumSettlements()` |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** Percentage and exact-amount split implementations
- **TODO:** Singleton for `UserManager`
- **TODO:** Group management (create groups, add/remove members)
- **TODO:** Expense categories and history
- **TODO:** Thread safety for concurrent expense creation
- **TODO:** Persistent storage / database integration

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `Split` (ABC) → `EqualSplit`, `PercentageSplit` | Swap splitting logic without modifying expense creation code |
| **Factory** | `SplitFactory.createSplit()` | Decouple split algorithm selection from client code |
| **Observer** | `Observer` (ABC) → `BalanceSheet` on `ExpenseManager` | Auto-update balances when expenses are added; decouples expense logic from balance tracking |

---

## Class Overview

```
User
    │  - id, name, email
    │
UserManager
    │  - users: Dict[int, User]
    │  - getUser(id)
    │
Split (ABC)  ◄── EqualSplit / PercentageSplit
    │  - split(amount, participants, splitDetails) → Dict[userId, share]
    │
SplitFactory
    │  - createSplit(splitType) → Split
    │
UserPair
    │  - payer, payee  (directed edge)
    │
Observer (ABC)  ◄── BalanceSheet
    │  - onExpenseUpdate(expense)
    │  - onExpenseAdded(expense)
    │
BalanceSheet
    │  - balances: Dict[UserPair, float]
    │  - updateBalances(expense)
    │  - getBalance(user1, user2) → net amount
    │  - getTotalBalance(user) → net overall
    │  - getSimplifiedSettlements() → List[Transaction]       (greedy)
    │  - getSubOptimalMinimumSettlements() → int              (backtracking DFS)
    │  - getOptimalMinimumSettlements() → int                 (bitmask DP)
    │
Expense
    │  - id, description, amount, payer, participants, shares, splitType
    │
ExpenseManager
    │  - expenses[], observers[]
    │  - addExpense(expense)
    │
Transaction
    │  - payee, payer, amount
```

---

## Settlement Algorithms

### 1. Simplified Settlements (Greedy)

Compute net balances → separate into creditors and debtors → greedily match them.

- **Time:** O(n) where n = number of users
- **Optimality:** Not guaranteed minimum transactions, but simple and fast.

### 2. Backtracking DFS (Sub-Optimal Minimum)

Try all possible pairings of debtors and creditors with opposite-sign balances.

- **Time:** O((n-1)!) — exponential, but explores minimum transaction count via backtracking.
- **Optimality:** Always correct (minimum transactions).

### 3. Bitmask DP (Optimal Minimum)

Find the maximum number of subsets whose balances sum to zero → answer = n - max_zero_subsets.

- **Time:** O(3^n) — iterate over all subsets and their sub-subsets.
- **Optimality:** Correct and more efficient than DFS for small n.

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — equal split only? groups in scope? settlement algorithms needed?
2. **Identify** classes top-down (3 min) — User, Split Strategy, Expense, BalanceSheet, Settlement.
3. **Code** core classes in order (35 min):
   - User + UserManager → Split hierarchy + Factory → Expense + ExpenseManager → BalanceSheet (Observer) → Settlement algorithms
4. **Mention** TODO features verbally (2 min) — groups, percentage split, persistence.
5. **Dry-run** a settlement (3 min) — A pays ₹300 split equally among A, B, C → B owes A ₹100, C owes A ₹100 → simplified: 2 transactions.